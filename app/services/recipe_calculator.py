from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product_option import ProductOption
from app.models.recipe import Recipe
from app.models.recipe_item import RecipeItem


class RecipeCalculator:
    """Serviço centralizado para cálculo de receitas com opções - EVITA DUPLICAÇÃO DE LÓGICA"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_final_recipe(
        self,
        base_product_id: int,
        selected_options: List[Dict[str, Any]],
        quantity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calcula a receita final aplicando todas as opções selecionadas
        
        Fluxo:
        1. Carrega receita base
        2. Aplica remoções
        3. Aplica adições
        4. Aplica multiplicadores
        5. Retorna snapshot final
        """
        
        # 1. Carregar receita base
        base_recipe = self._load_base_recipe(base_product_id)
        if not base_recipe:
            return {"ingredients": [], "total_multiplier": 1.0}
        
        # 2. Iniciar com ingredientes base
        final_ingredients = {}
        for item in base_recipe.get("ingredients", []):
            key = str(item["ingredient_product_id"])
            final_ingredients[key] = {
                "ingredient_product_id": item["ingredient_product_id"],
                "qty": float(item["qty"]) * quantity,
                "unit": item["unit"],
                "waste_percent": float(item.get("waste_percent", 0))
            }
        
        # 3. Aplicar opções selecionadas
        total_multiplier = 1.0
        applied_options = []
        
        for option_data in selected_options:
            option = self._get_option_by_id(option_data.get("option_id"))
            if not option:
                continue
                
            applied_options.append({
                "option_id": option.id,
                "option_name": option.name,
                "option_type": option.option_type,
                "price_adjustment": float(option.price_adjustment)
            })
            
            # Aplicar lógica baseada no tipo
            if option.option_type == "variant":
                # Variantes afetam multiplicadores
                total_multiplier *= self._extract_multiplier(option.ingredient_multiplier)
                
            elif option.option_type == "addon":
                # Addons apenas adicionam ingredientes
                self._apply_additions(final_ingredients, option.ingredient_impact, quantity)
                
            elif option.option_type == "removal":
                # Removals removem ingredientes
                self._apply_removals(final_ingredients, option.ingredient_remove)
        
        # 4. Aplicar multiplicador total em todos os ingredientes
        if total_multiplier != 1.0:
            for ingredient in final_ingredients.values():
                ingredient["qty"] *= total_multiplier
        
        return {
            "ingredients": list(final_ingredients.values()),
            "total_multiplier": total_multiplier,
            "applied_options": applied_options,
            "base_recipe_id": base_recipe.get("recipe_id")
        }
    
    def calculate_price_with_options(
        self,
        base_price: float,
        selected_options: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calcula preço final aplicando ajustes das opções"""
        
        final_price = base_price
        options_total = 0.0
        
        for option_data in selected_options:
            option = self._get_option_by_id(option_data.get("option_id"))
            if not option:
                continue
                
            adjustment = float(option.price_adjustment)
            
            if option.adjustment_type == "percentage":
                adjustment = base_price * (adjustment / 100.0)
            
            final_price += adjustment
            options_total += adjustment
        
        return {
            "final_price": final_price,
            "base_price": base_price,
            "options_total": options_total
        }
    
    def _load_base_recipe(self, product_id: int) -> Dict[str, Any] | None:
        """Carrega a receita base de um produto"""
        recipe = self.db.scalar(
            select(Recipe)
            .where(Recipe.product_id == product_id)
            .where(Recipe.is_active == True)
            .order_by(Recipe.id.desc())
        )
        
        if not recipe:
            return None
        
        recipe_items = self.db.scalars(
            select(RecipeItem)
            .where(RecipeItem.recipe_id == recipe.id)
            .order_by(RecipeItem.id.asc())
        ).all()
        
        return {
            "recipe_id": recipe.id,
            "ingredients": [
                {
                    "ingredient_product_id": item.ingredient_product_id,
                    "qty": float(item.qty),
                    "unit": item.unit,
                    "waste_percent": float(item.waste_percent)
                }
                for item in recipe_items
            ]
        }
    
    def _get_option_by_id(self, option_id: int) -> ProductOption | None:
        """Busca uma opção pelo ID"""
        return self.db.get(ProductOption, option_id)
    
    def _apply_additions(self, ingredients: Dict, impact_data: Dict, quantity: float):
        """Aplica adições de ingredientes"""
        additions = impact_data.get("add", {})
        
        for product_id_str, ingredient_data in additions.items():
            product_id = int(product_id_str)
            key = str(product_id)
            
            if key not in ingredients:
                ingredients[key] = {
                    "ingredient_product_id": product_id,
                    "qty": 0,
                    "unit": ingredient_data.get("unit", "un"),
                    "waste_percent": 0
                }
            
            ingredients[key]["qty"] += float(ingredient_data.get("qty", 0)) * quantity
    
    def _apply_removals(self, ingredients: Dict, remove_data: Dict):
        """Aplica remoções de ingredientes"""
        removals = remove_data.get("remove", [])
        
        for product_id in removals:
            key = str(product_id)
            if key in ingredients:
                del ingredients[key]
    
    def _extract_multiplier(self, multiplier_data: Dict) -> float:
        """Extrai multiplicador dos dados da opção"""
        multipliers = multiplier_data.get("multiply", {})
        
        # Se não houver multiplicadores específicos, retorna 1.0
        if not multipliers:
            return 1.0
        
        # Por enquanto, usa o primeiro multiplicador encontrado
        # Em um cenário mais complexo, poderia ter lógica diferente
        first_multiplier = list(multipliers.values())[0]
        return float(first_multiplier)


def create_recipe_calculator(db: Session) -> RecipeCalculator:
    """Factory function para criar RecipeCalculator"""
    return RecipeCalculator(db)
