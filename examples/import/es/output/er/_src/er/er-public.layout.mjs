export default {
  "model": "er.model.json",
  "schema": "public",
  "title": "Diagrama importado",
  "sub": "Contenido del archivo de entrada. El motor recalcula la disposición de los elementos.",
  "canvas": {
    "w": 1700
  },
  "tables": {
    "public.CUSTOMER": {
      "x": 700,
      "y": 60,
      "w": 500,
      "desc": "CUSTOMER"
    },
    "public.ORDER": {
      "x": 700,
      "y": 238,
      "w": 500,
      "desc": "ORDER"
    }
  },
  "edges": [
    {
      "from": "public.ORDER",
      "column": "customer_id",
      "exit": "L",
      "to": "public.CUSTOMER",
      "enter": "L",
      "lane": 650,
      "dy": 14,
      "text": "El cliente tiene pedidos"
    }
  ],
  "lang": "es"
};
