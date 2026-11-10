workspace "Loja on-line" {
    model {
        cliente = person "Cliente" "compra na loja web"
        loja = softwareSystem "Loja on-line" "vende e entrega pedidos" {
            web = container "Loja web" "catálogo e pagamento" "Next.js" "Navegador"
            api = container "API de pedidos" "recebe e acompanha os pedidos" "Node.js"
            db = container "Banco de pedidos" "pedidos e pagamentos" "PostgreSQL" "Banco"
        }
        pagamentos = softwareSystem "Provedor de pagamentos" "cobra o cartão" "External"
        cliente -> web "Faz pedidos" "navegador"
        web -> api "Envia o pedido" "HTTPS · JSON"
        api -> db "Grava o pedido" "SQL"
        api -> pagamentos "Cobra o cartão" "HTTPS"
    }
    views {
        container loja "conteineres" "Os contêineres da loja on-line." {
            include *
            autoLayout
        }
        styles {
            element "Navegador" { shape WebBrowser }
            element "Banco" { shape Cylinder }
        }
    }
}
