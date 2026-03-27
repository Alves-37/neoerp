# Formatos JSON - Sistema de Opções de Produtos

## 📋 Visão Geral

Este documento descreve os formatos JSON para o sistema avançado de opções de produtos, projetado para restaurantes com controle inteligente de stock.

## 🎯 Tipos de Opções

### 1. **variant** (Variação)
Muda a base do produto (tamanho, tipo, etc.)
- Exemplo: "Pequeno", "Médio", "Grande"
- Impacto: Multiplicadores de ingredientes
- Preço: Ajuste fixo ou percentual

### 2. **addon** (Adicional)
Adiciona ingredientes extras
- Exemplo: "Bacon Extra", "Queijo Extra"
- Impacto: Adição de ingredientes
- Preço: Ajuste fixo

### 3. **removal** (Remoção)
Remove ingredientes da receita base
- Exemplo: "Sem Queijo", "Sem Cebola"
- Impacto: Remoção de ingredientes
- Preço: Desconto (valor negativo)

## 📄 Formatos JSON

### ingredient_impact (Adições)
```json
{
  "add": {
    "123": {
      "qty": 0.05,
      "unit": "kg"
    },
    "456": {
      "qty": 1,
      "unit": "un"
    }
  }
}
```

### ingredient_remove (Remoções)
```json
{
  "remove": [123, 456, 789]
}
```

### ingredient_multiplier (Multiplicadores)
```json
{
  "multiply": {
    "123": 1.5,
    "456": 2.0
  }
}
```

## 🍽️ Exemplos Práticos

### Exemplo 1: Hambúrguer com Tamanhos

#### Produto Base: Hambúrguer
- Receita: 150g carne, 1 pão, 1 queijo
- Preço: 100 MT

#### Opções de Tamanho (variant)
```json
// "Pequeno"
{
  "option_type": "variant",
  "price_adjustment": -20,
  "ingredient_multiplier": {
    "multiply": {
      "123": 0.8  // 80% da carne
    }
  }
}

// "Grande"  
{
  "option_type": "variant",
  "price_adjustment": 50,
  "ingredient_multiplier": {
    "multiply": {
      "123": 1.5  // 150% da carne
    }
  }
}
```

#### Opções de Extras (addon)
```json
// "Bacon Extra"
{
  "option_type": "addon",
  "price_adjustment": 30,
  "ingredient_impact": {
    "add": {
      "789": {
        "qty": 0.05,
        "unit": "kg"
      }
    }
  }
}
```

#### Opções de Remoção (removal)
```json
// "Sem Queijo"
{
  "option_type": "removal",
  "price_adjustment": -15,
  "ingredient_remove": {
    "remove": [456]  // ID do queijo
  }
}
```

### Fluxo Completo: "Hambúrguer Grande + Bacon Extra + Sem Queijo"

#### 1. Receita Base
- Carne (123): 150g
- Pão (234): 1 un
- Queijo (456): 1 un

#### 2. Aplicar "Grande" (variant)
- Carne: 150g × 1.5 = 225g
- Pão: 1 un (sem mudança)
- Queijo: 1 un (sem mudança)

#### 3. Aplicar "Bacon Extra" (addon)
- + Bacon (789): 50g

#### 4. Aplicar "Sem Queijo" (removal)
- - Queijo (456): removido

#### 5. Resultado Final
- Carne (123): 225g
- Pão (234): 1 un
- Bacon (789): 50g
- Preço: 100 + 50 + 30 - 15 = 165 MT

## 🔧 Integração com Stock

O sistema calcula automaticamente:

1. **Consumo Base**: Multiplicado pela quantidade do pedido
2. **Adições**: Somadas ao consumo base
3. **Remoções**: Subtraídas do consumo base
4. **Multiplicadores**: Aplicados nos ingredientes especificados

## ⚡ Performance

- **Snapshot**: Receita final calculada é salva para auditoria
- **Cache**: Cálculos feitos uma vez no momento da venda
- **Consistência**: Evita recálculos e garante integridade

## 🎯 Benefícios

✅ **Controle Preciso**: Cada ingrediente é rastreado
✅ **Flexibilidade Total**: Suporta qualquer combinação
✅ **Performance**: Cálculos otimizados e cacheados
✅ **Auditoria**: Tudo registrado para análise
✅ **Escalabilidade**: Funciona para qualquer complexidade
