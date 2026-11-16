workspace "Sistema de cobrança por boleto" "Modelo C4 do exemplo de cobrança" {
    !identifiers flat

    model {
        enterprise "Empresa" {
            cliente = person "Cliente PJ" "emite boletos e acompanha os pagamentos"
            analista = person "Analista financeiro" "trata pagamento em duplicidade e devolução"
            cobranca = softwareSystem "Sistema de cobrança" "emite o boleto, registra na CIP e dá baixa pelo arquivo de retorno" {
                portal = container "Portal PJ" "emissão em lote e painel de recebimentos" "Next.js na Vercel" "Navegador"
                backoffice = container "Backoffice" "consulta e ajuste manual de boletos" "React" "Navegador"
                api = container "API de cobrança" "atrás do API Gateway; valida o pagador e grava o boleto" "Node.js em Lambda" {
                    rotas = component "Rotas de boleto" "recebe a emissão, a consulta e o ajuste" "Fastify"
                    acesso = component "Controle de acesso" "confere se quem chama é cliente ou operador" "JWT da Cognito"
                    pagador = component "Validador de pagador" "confere CPF ou CNPJ, vencimento e valor" "TypeScript"
                    registro = component "Registro na CIP" "registra o boleto e devolve a linha digitável" "cliente HTTPS com certificado"
                    repositorio = component "Repositório de boletos" "lê e grava boleto, situação e evento" "AWS SDK"
                }
                banco = container "Banco de cobrança" "boletos, situação e histórico de eventos" "DynamoDB" "Banco"
                processador = container "Processador de retorno" "lê o arquivo de retorno e dá baixa no boleto" "Lambda e fila SQS"
            }
            erp = softwareSystem "ERP contábil" "registra o lançamento de cada baixa" {
            }
        }
        cip = softwareSystem "Nova Plataforma de Cobrança" "registro do boleto"
        liquidante = softwareSystem "Banco liquidante" "gera o arquivo CNAB 240 de retorno"
        webhook = softwareSystem "Webhook do cliente" "recebe o aviso de boleto pago"

        cliente -> cobranca "Emite e acompanha boletos" "portal web ou API"
        cliente -> portal "Emite boletos e acompanha recebimentos" "navegador"
        cliente -> rotas "Integra o próprio sistema para emitir e consultar" "HTTPS · JSON"
        analista -> backoffice "Trata duplicidade e devolução" "navegador"
        portal -> rotas "Pede a emissão e consulta a situação" "HTTPS · JSON"
        backoffice -> rotas "Ajusta boletos com papel de operador" "HTTPS · JSON"
        rotas -> acesso "Confere o papel de quem chama" "chamada interna"
        rotas -> pagador "Valida o pedido de emissão" "chamada interna"
        rotas -> registro "Pede o registro do boleto" "chamada interna"
        rotas -> repositorio "Grava e consulta boletos" "chamada interna"
        registro -> cip "Registra o boleto antes da linha digitável" "HTTPS · certificado"
        repositorio -> banco "Grava boleto, situação e evento" "DynamoDB API"
        liquidante -> processador "Entrega o CNAB 240 de retorno" "SFTP → S3 → SQS"
        processador -> banco "Dá baixa e grava o pagamento" "DynamoDB API"
        processador -> webhook "Avisa cada boleto pago" "HTTPS · HMAC"
        processador -> erp "Publica o lançamento da baixa" "EventBridge"

        deploymentEnvironment "producao" {
            aws = deploymentNode "Conta AWS cobranca-prod" "" "sa-east-1" {
                gateway = infrastructureNode "API pública" "termina o TLS e confere o token" "Amazon API Gateway, com WAF"
                lambda-api = deploymentNode "AWS Lambda" "" "Node.js 20" {
                    api-1 = containerInstance api
                }
                dynamo = deploymentNode "Amazon DynamoDB" "" "sob demanda" {
                    banco-1 = containerInstance banco
                }
                bucket = infrastructureNode "Caixa de retorno" "recebe o CNAB 240 por SFTP" "Amazon S3, via Transfer Family"
                fila = infrastructureNode "Fila de retorno" "um evento por arquivo novo" "Amazon SQS"
                lambda-ret = deploymentNode "AWS Lambda" "" "Node.js 20" {
                    processador-1 = containerInstance processador
                }
            }
            vercel = deploymentNode "Vercel" "" "rede de borda" {
                portal-1 = containerInstance portal
            }
            cdn = deploymentNode "Amazon CloudFront" "" "site estático no S3" {
                backoffice-1 = containerInstance backoffice
            }
            gateway -> api-1 "Encaminha a chamada autenticada" "integração Lambda"
            bucket -> fila "Avisa arquivo novo" "evento do S3"
            fila -> processador-1 "Aciona com o arquivo" "gatilho SQS"
        }
    }

    views {
        systemLandscape "landscape" "Quem usa a cobrança por boleto e com que sistemas, de dentro e de fora da empresa, ela conversa." {
            title "Cobrança por boleto: sistemas e pessoas"
            include *
            autoLayout
        }
        systemContext cobranca "context" "O sistema de cobrança como uma caixa só: quem o usa e de que sistemas ele depende. Pix cobrança, protesto e negativação ficam fora." {
            title "Sistema de cobrança: contexto"
            include *
            autoLayout
        }
        container cobranca "containers" "Em que contêineres o sistema de cobrança se divide e de que sistemas ele depende, da emissão do boleto à baixa pelo arquivo de retorno. Pix cobrança, protesto e negativação ficam fora do desenho." {
            title "Sistema de cobrança por boleto: contêineres e dependências"
            include *
            autoLayout
        }
        component api "api" "As partes da API de cobrança e quem chama cada uma, do pedido de emissão ao registro na CIP e à gravação no banco." {
            title "API de cobrança: componentes"
            include *
            autoLayout
        }
        dynamic cobranca "emission" "O caminho de um pedido de emissão feito no portal, até o cliente receber a linha digitável." {
            title "Emissão de um boleto pelo portal"
            cliente -> portal "Preenche pagador, valor e vencimento" "navegador"
            portal -> api "Envia o pedido de emissão" "HTTPS · JSON"
            api -> cip "Registra o boleto e recebe a linha digitável" "HTTPS · certificado"
            api -> banco "Grava o boleto como registrado" "DynamoDB API"
            portal -> cliente "Mostra a linha digitável e o PDF" "navegador"
            autoLayout
        }
        deployment cobranca producao "deployment" "Onde cada contêiner roda em produção: as funções e o banco numa conta AWS, o portal na Vercel e o backoffice no CloudFront." {
            title "Sistema de cobrança: implantação em produção"
            include *
            autoLayout
        }

        styles {
            element "Navegador" {
                shape WebBrowser
            }
            element "Banco" {
                shape Cylinder
            }
        }
    }
}
