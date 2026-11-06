export default {
  "modelo": "er.modelo.json",
  "schema": "public",
  "titulo": "Imported diagram",
  "sub": "Content from the input file. The engine recalculates the layout of the elements.",
  "canvas": {
    "w": 1700
  },
  "tabelas": {
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
  "arestas": [
    {
      "de": "public.ORDER",
      "coluna": "customer_id",
      "sai": "L",
      "para": "public.CUSTOMER",
      "chega": "L",
      "raia": 650,
      "dy": 14,
      "texto": "Customer has orders"
    }
  ],
  "idioma": "en"
};
