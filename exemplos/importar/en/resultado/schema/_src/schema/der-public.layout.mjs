export default {
  "modelo": "schema.modelo.json",
  "schema": "public",
  "titulo": "public",
  "sub": "Content from the input file. The engine recalculates the layout of the elements.",
  "canvas": {
    "w": 1700
  },
  "tabelas": {
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
  "arestas": [
    {
      "de": "public.orders",
      "coluna": "customer_id",
      "sai": "L",
      "para": "public.customers",
      "chega": "L",
      "raia": 650,
      "dy": 14,
      "texto": "public.orders.customer_id → public.customers"
    }
  ],
  "idioma": "en"
};
