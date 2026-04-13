#!/usr/bin/env zsh

# set error handling
set -e

# constants
REPO_URL="https://github.com/CDCgov/dibbs-ecr-refiner.git"
REPO_DIR="dibbs-ecr-refiner"
APP_URL="http://localhost:8081/"
DOCKER_DEFAULT_PLATFORM=$(_get_system_arch())

# function to get the user's system architecture in the way Docker expects
_get_system_arch() {
  local arch=$(uname -m)
  if [ "${arch}" = "x86_64" ]; then
    echo "linux/amd64"
  elif [ "${arch}" = "arm64" ]; then
    echo "linux/arm64"
  fi
}

# function to display error messages and exit
error_exit() {
    echo -e "❌ Error:\n\t$1" >&2
    exit 1
}

# function to check for required commands and install if missing
ensure_command() {
    local command_name=$1
    local install_command=$2

    if ! command -v "$command_name" &> /dev/null; then
        echo -e "🔍 $command_name not found, installing..."
        eval "$install_command" || error_exit "Failed to install $command_name"
        echo -e "✅ Successfully installed $command_name"
    fi
}

# function to wait for service availability
wait_for_service() {
    local url=$1
    local message=$2

    echo -e "⏳ $message"
    until curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; do
        echo -e "🔄 Waiting for service to be available..."
        sleep 5
    done
}

# check if branch name is provided
if [[ -z "$1" ]]; then
    error_exit "Did you forget the branch name?\n💡 Try:\n\t$0 <branch-name>"
fi

BRANCH_NAME="$1"
echo -e "🚀 Starting design review setup for branch: $BRANCH_NAME\n"

# only install homebrew if it's missing (no update)
if ! command -v brew &> /dev/null; then
    echo -e "🍺 Homebrew not found, installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || \
        error_exit "Failed to install Homebrew"
fi

# ensure required tools are installed
ensure_command "git" "brew install git"
ensure_command "just" "brew install just"
ensure_command "docker" "brew install --cask docker"
ensure_command "docker-compose" "brew install docker-compose"

# start docker if not running
if ! docker info &> /dev/null; then
    echo -e "🐳 Starting Docker..."
    open -a Docker
    while ! docker system info &> /dev/null; do
        echo -e "⏳ Waiting for Docker to start..."
        sleep 2
    done
fi

# repository handling
echo -e "📦 Setting up repository..."
if [[ ! -d "$REPO_DIR" ]]; then
    echo -e "🔍 Repository not found locally, cloning..."
    git clone "$REPO_URL" || error_exit "Failed to clone repository"
    cd "$REPO_DIR" || error_exit "Failed to enter repository directory"
else
    cd "$REPO_DIR" || error_exit "Failed to enter repository directory"
    echo -e "🔄 Updating existing repository..."
    git fetch origin
fi

# checkout specified branch
echo -e "🔄 Checking out branch: $BRANCH_NAME"
git checkout "$BRANCH_NAME" || error_exit "Failed to checkout branch: $BRANCH_NAME"
git pull origin "$BRANCH_NAME" || error_exit "Failed to pull latest changes"

# build and run containers
echo -e "🏗️ Building and starting containers..."
docker-compose build --no-cache && docker-compose up -d || error_exit "Failed to start containers"

# Wipe the local database
echo -e "🧹 Cleaning up data..."
just db clean

# Run database migrations
echo -e "💻 Running database migrations..."
just migrate local

# Run seed script
echo -e "🩺 Seeding database with condition data..."
just db seed

# wait for application to be available
wait_for_service "$APP_URL" "Waiting for application to start..."

# open in default browser
echo -e "🌐 Opening application in browser..."
open "$APP_URL"

echo -e "🎉 Review environment is ready!\n"
echo -e "👋 Press Enter to end review and cleanup containers..."
read -r
docker-compose down
echo -e "✨ Cleanup complete!"
