export default {
  "model": "er.model.json",
  "schema": "public",
  "title": "Diagrama importado",
  "sub": "Conteúdo do arquivo de entrada. O motor recalcula a disposição dos elementos.",
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
      "text": "Cliente possui pedidos"
    }
  ],
  "lang": "pt-BR"
};
