# Краткое описание 
Проект состоит из прокси сервера `proxy-server.py` и тестовых серверов, которые принимают аргументом формат сериализации. В зависимости от формата тестовый сервер поднимается на определенном порту (прописан в `docker-compose.yml`) и слушает запросы на сериализацию. 

Когда пользователь делает запрос прокси серверу, тот в зависимости от формата сериализации перенаправляет его на соответствующий тестовый сервер. 

Для прокси сервера и каждого `test_server` для определенного формата я сделала docker контейнер. 

## Данные 

Сериализуется структура, поля которой генерируются случайно: 

```
struct House {
    name: String,  
    materials: [String],  
    owners: Map<String, int>,  
    year_built: int,  
    square: float,  
}
```

### Сделана продвинутая версия дз

# Как запускать 

## Серверы
`docker-compose build && docker-compose up -d`

## Запросы

`echo "get_result {format_name}" | nc -u localhost 2000`

`format_name` может быть один из: `XML`, `JSON`, `PBUFFER`, `MPACK`, `NAIVE`, `AVRO`, `YAML`. Регистр важен.



# Результаты 

**Формат**: {format_name} - {size of serialized_data} - {serialization_time}ms - {deserialization_time}ms"

`XML - 841 - 1.445ms - 0.566ms`

`JSON - 381 - 0.065ms - 0.044ms`

`PBUFFER - 255 - 1.248ms - 0.004ms`

`MPACK - 268 - 0.053ms - 0.038ms`

`NAIVE - 335 - 0.811ms - 0.014ms`

`AVRO - 218 - 0.337ms - 0.205ms`

`YAML - 349 - 1.131ms - 1.909ms`