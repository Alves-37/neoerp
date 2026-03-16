def get_default_branches() -> list[tuple[str, str]]:
    return [
        ("Filial Retalho", "retail"),
        ("Filial Mercearia", "grocery"),
        ("Filial Peixaria", "fish"),
        ("Filial Mercearia e Peixaria", "grocery_fish"),
        ("Filial Restaurante", "restaurant"),
        ("Filial Bar", "bar"),
        ("Filial Açougue", "butcher"),
        ("Filial Serviços", "services"),
        ("Filial Farmácia", "pharmacy"),
        ("Filial Reprografia", "reprography"),
    ]
