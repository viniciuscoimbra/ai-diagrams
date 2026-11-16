workspace "Tienda en línea" {
    model {
        cliente = person "Cliente" "compra en la tienda web"
        tienda = softwareSystem "Tienda en línea" "vende y envía pedidos" {
            web = container "Tienda web" "catálogo y pago" "Next.js" "Navegador"
            api = container "API de pedidos" "recibe y sigue los pedidos" "Node.js"
            db = container "Base de pedidos" "pedidos y pagos" "PostgreSQL" "Base"
        }
        pagos = softwareSystem "Proveedor de pagos" "cobra la tarjeta" "External"
        cliente -> web "Hace pedidos" "navegador"
        web -> api "Envía el pedido" "HTTPS · JSON"
        api -> db "Guarda el pedido" "SQL"
        api -> pagos "Cobra la tarjeta" "HTTPS"
    }
    views {
        container tienda "contenedores" "Los contenedores de la tienda en línea." {
            include *
            autoLayout
        }
        styles {
            element "Navegador" { shape WebBrowser }
            element "Base" { shape Cylinder }
        }
    }
}
