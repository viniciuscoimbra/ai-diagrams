workspace "Online store" {
    model {
        customer = person "Customer" "buys from the web store"
        store = softwareSystem "Online store" "sells and ships orders" {
            web = container "Web store" "catalog and checkout" "Next.js" "Browser"
            api = container "Orders API" "takes and tracks orders" "Node.js"
            db = container "Orders database" "orders and payments" "PostgreSQL" "Database"
        }
        payments = softwareSystem "Payment provider" "charges the card" "External"
        customer -> web "Places orders" "browser"
        web -> api "Sends the order" "HTTPS · JSON"
        api -> db "Stores the order" "SQL"
        api -> payments "Charges the card" "HTTPS"
    }
    views {
        container store "containers" "The containers of the online store." {
            include *
            autoLayout
        }
        styles {
            element "Browser" { shape WebBrowser }
            element "Database" { shape Cylinder }
        }
    }
}
