workspace {
    !identifiers hierarchical

    model {
        properties {
            "structurizr.groupSeparator" "/"
        }

        // dev = person "eCR Developer" {
        //     description "A developer of the DIBBs eCR Refiner platform"
        // }

        user = person "Jurisdiction User" {
            description "A jurisdiction user of the DIBBs eCR Refiner platform"
        }

        refiner = softwareSystem "DIBBs eCR Refiner" {
            description "The DIBBs eCR Refiner platform"
            tags "DIBBs"

            group "Network Layer" {
                network = container "Virtual Network" {
                    description "Virtual network for the DIBBs eCR Refiner platform"
                    tags "Microsoft Azure - Virtual Networks"
                }
                auth = container "Authentication \n Service" {
                    description "Handles user authentication and authorization"
                    technology "Keycloak"
                    tags "Keycloak" "Authentication"
                }

                fusion_auth = container "FusionAuth" {
                    description "Handles user authentication and authorization"
                    technology "FusionAuth"
                    tags "FusionAuth" "Authentication"
                }
            }

            group "Data Layer" {
                database = container "Database" {
                    description "Database for storing application data"
                    technology "PostgreSQL"
                    tags "Microsoft Azure - Azure Database PostgreSQL Server"
                }
                storage = container "Storage Account" {
                    description "Storage account for storing application data"
                    technology "Azure Blob Storage"
                    tags "Microsoft Azure - Storage Accounts"
                }
            }

            localstack = container "LocalStackdocs/workspace/diagrams/structurizr/**/*.json -diff0" {
                description "S3-compatible API local development and testing"
                technology "LocalStack"
                tags "LocalStack" "Development"
            }

            registry = container "Container Registry" {
                description "Container registry for storing Docker images"
                technology "Azure Container Registry"
                tags "Microsoft Azure - Container Registries"
            }

            group "Public VPC" {
                api = container "API" {
                    description "Handles all HTTPS API requests"
                    technology "Python, FastAPI"
                    tags "Microsoft Azure - Container Instances" "API"
                }
                app = container "Application" {
                    description "Frontend application for user interaction"
                    technology "React, TypeScript"
                    tags "Web App" "React Application"
                }
            }

            group "Private VPC" {
                sqs = container "Message Queue" {
                    description "Message queue for handling asynchronous tasks"
                    technology "AWS SQS"
                    tags "Amazon Web Services - Simple Queue Service Message"
                }

                lambda = container "Refiner Lambda" {
                    description "Serverless function for refinement tasks"
                    technology "Python, AWS Lambda"
                    tags "Amazon Web Services - Lambda"
                }
            }
        }

        // Azure Relationships
        user -> refiner.network "Navigates to Refiner Application"
        refiner.network -> refiner.app "Redirects to"
        refiner.app -> refiner.fusion_auth "Authenticates the user"
        refiner.fusion_auth -> refiner.app "Provides authentication tokens to"
        refiner.app -> refiner.api "Communicates with token to"
        refiner.api -> refiner.database "Reads from and writes to"
        refiner.api -> refiner.storage "Reads from and writes to"
        refiner.api -> refiner.localstack "Reads from and writes to"

        // AWS Relationships
        refiner.storage -> refiner.sqs "Sends messages to"
        refiner.sqs -> refiner.lambda "Triggers"
        refiner.lambda -> refiner.storage "Reads from and writes to"


        // development = deploymentEnvironment "Development" {
        //     deploymentNode "Developer Laptop" {
        //         description "Laptop used by developers to develop and test the application"
        //         containerInstance refiner.app {
        //             description "Runs the frontend application locally"
        //         }
        //         containerInstance refiner.api {
        //             description "Runs the API locally"
        //         }
        //         containerInstance refiner.auth {
        //             description "Runs the authentication service locally"
        //         }
        //         deploymentNode "LocalStack" {
        //             containerInstance refiner.localstack {
        //                 description "Runs an S3-compatible API locally"
        //             }
        //         }
        //         deploymentNode "PostgreSQL Database" {
        //             tags "Database"
        //             containerInstance refiner.database {
        //                 description "Runs the PostgreSQL database locally"
        //             }
        //         }
        //     }
        // }
    }

    views {

        systemLandscape "refiner-system-landscape" {
            include *
            autolayout lr
            title "DIBBs eCR Refiner - System Landscape"
            description "The system landscape diagram for the DIBBs eCR Refiner platform"
        }

        // systemContext refiner "refiner-system-context" {
        //     include *
        //
        //     title "DIBBs eCR Refiner - System Context"
        //     description "The system context diagram for the DIBBs eCR Refiner platform"
        // }

        // container refiner "refiner-application-azure" {
        //     include *
        //     exclude refiner.registry refiner.localstack refiner.auth
        //
        //     title "DIBBs eCR Refiner - Application"
        //     description "The application diagram for the DIBBs eCR Refiner platform"
        // }

        // deployment * development "local-development" {
        //     include *
        //     autolayout lr
        // }

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
                background "#dbf6ff"
                stroke "#3b7082"
                color "#3b7082"
                shape "WebBrowser"
            }

            element "DIBBs" {
                background "#facc2e"
                color "#000000"
                stroke "#000000"
            }

            element "Group:Refiner API & Client UI" {
                color "#3b7082"
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
