export default {
  "model": "schema.model.json",
  "schema": "public",
  "title": "public",
  "sub": "Contenido del archivo de entrada. El motor recalcula la disposición de los elementos.",
  "canvas": {
    "w": 1700
  },
  "tables": {
    "public.customers": {
      "x": 700,
      "y": 60,
      "w": 500,
      "desc": "customers"
    },
    "public.orders": {
      "x": 700,
      "y": 238,
      "w": 500,
      "desc": "orders"
    }
  },
  "edges": [
    {
      "from": "public.orders",
      "column": "customer_id",
      "exit": "L",
      "to": "public.customers",
      "enter": "L",
      "lane": 650,
      "dy": 14,
      "text": "public.orders.customer_id → public.customers"
    }
  ],
  "lang": "es"
};
