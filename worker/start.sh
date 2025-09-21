#!/bin/bash

# Worker Service Startup Script
# This script helps set up and run the RepoCanvas Worker Service

set -e

echo "🚀 RepoCanvas Worker Service Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
}

# Check if Git is installed
check_git() {
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_status "Git $GIT_VERSION found"
    else
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi
}

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker found"
        return 0
    else
        print_warning "Docker not found. Docker is optional but recommended for Qdrant."
        return 1
    fi
}

# Create virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Installing requirements..."
    pip install -r requirements.txt
}

# Setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please review and adjust .env file settings as needed"
    else
        print_status ".env file already exists"
    fi
}

# Create data directories
setup_directories() {
    print_status "Creating data directories..."
    mkdir -p data/documents
    mkdir -p data/graphs
    mkdir -p tmp/repos
}

# Start Qdrant with Docker
start_qdrant() {
    if check_docker; then
        print_status "Starting Qdrant with Docker..."
        if docker ps | grep -q qdrant_db; then
            print_status "Qdrant is already running"
        else
            docker-compose up -d qdrant
            print_status "Waiting for Qdrant to be ready..."
            sleep 10
            
            # Check if Qdrant is responding
            for i in {1..30}; do
                if curl -f http://localhost:6333/health &> /dev/null; then
                    print_status "Qdrant is ready!"
                    break
                elif [ $i -eq 30 ]; then
                    print_error "Qdrant failed to start"
                    exit 1
                else
                    sleep 2
                fi
            done
        fi
    else
        print_warning "Docker not available. Please start Qdrant manually or install Docker."
        print_warning "You can download Qdrant from: https://qdrant.tech/documentation/quick-start/"
    fi
}

# Start the worker service
start_worker() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    print_status "Starting Worker Service..."
    python app.py
}

# Main setup function
setup() {
    print_status "Setting up RepoCanvas Worker Service..."
    
    check_python
    check_git
    setup_directories
    setup_env
    setup_venv
    
    print_status "Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review and adjust .env file settings"
    echo "2. Start Qdrant: ./start.sh qdrant"
    echo "3. Start Worker: ./start.sh worker"
    echo "4. Run tests: ./start.sh test"
}

# Help function
show_help() {
    echo "RepoCanvas Worker Service Startup Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initial setup (install dependencies, create directories)"
    echo "  qdrant    - Start Qdrant database"
    echo "  worker    - Start the worker service"
    echo "  all       - Start both Qdrant and worker"
    echo "  test      - Run API tests"
    echo "  stop      - Stop all services"
    echo "  clean     - Clean up containers and volumes"
    echo "  help      - Show this help message"
}

# Parse command line arguments
case "${1:-help}" in
    setup)
        setup
        ;;
    qdrant)
        start_qdrant
        ;;
    worker)
        start_worker
        ;;
    all)
        start_qdrant
        start_worker
        ;;
    test)
        print_status "Running API tests..."
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi
        python test_worker_api.py
        ;;
    stop)
        print_status "Stopping services..."
        if check_docker; then
            docker-compose down
        fi
        print_status "Services stopped"
        ;;
    clean)
        print_status "Cleaning up containers and volumes..."
        if check_docker; then
            docker-compose down -v
            docker system prune -f
        fi
        print_status "Cleanup complete"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
