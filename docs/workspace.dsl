workspace {
    !identifiers hierarchical

    model {
        properties {
            "structurizr.groupSeparator" "/"
        }

        user = person "Jurisdiction User" {
            description "A jurisdiction user of the DIBBs eCR Refiner platform"
        }

        refiner = softwareSystem "DIBBs eCR Refiner" {
            description "The DIBBs eCR Refiner platform"
            tags "DIBBs"

            network = container "Virtual Network" {
                description "Virtual network for the DIBBs eCR Refiner platform"
                tags "Microsoft Azure - Virtual Networks"
            }

            database = container "Database" {
                description "Database for storing application data"
                technology "Azure SQL Database"
                tags "Microsoft Azure - Azure Database PostgreSQL Server"
            }

            storage = container "Storage Account" {
                description "Storage account for storing application data"
                technology "Azure Blob Storage"
                tags "Microsoft Azure - Storage Accounts"
            }

            registry = container "Container Registry" {
                description "Container registry for storing Docker images"
                technology "Azure Container Registry"
                tags "Microsoft Azure - Container Registries"
            }

            api = container "API" {
                description "Handles all HTTPS API requests"
                technology "Python, FastAPI"
                tags "Microsoft Azure - Container Instances" "API"
            }
            app = container "Application" {
                description "Frontend application for user interaction"
                technology "React, TypeScript"
                tags "Amazon Web Services - S3" "Web App" "React Application"
            }
        }

        // Relationships
        user -> refiner.network "Navigates to Refiner Application"
        refiner.network -> refiner.app "Serves"
        refiner.app -> refiner.api "Makes API calls to"
        refiner.api -> refiner.database "Reads from and writes to"
        refiner.api -> refiner.storage "Reads from and writes to"
    }

    views {
        systemContext refiner {
            include *
        }

        container refiner {
            include *
            exclude refiner.registry
        }

        styles {
            element "Container" {
                background "#6CB5F3"
                color "#ffffff"
            }
            element "Component" {
                background "#85BB65"
                color "#ffffff"
            }
            element "Person" {
                background "#6e99b2"
                stroke "#afcadb"
                color "#ffffff"
                shape "Person"
            }
            element "Web App" {
                shape "WebBrowser"
            }

            element "DIBBs" {
                background "#facc2e"
                color "#000000"
                stroke "#000000"
            }

            theme "./styles/theme.json"

        }
        branding {
            logo "./styles/.icons/skylight-logo.png"
            font "Libre Franklin" "https://fonts.googleapis.com/css2?family=Libre+Franklin:ital,wght@0,100..900;1,100..900&display=swap"
        }
        properties {
            "structurizr.locale" "en-US"
            "structurizr.timezone" "America/New_York"
        }
    }

    configuration {
        scope none
    }
}
