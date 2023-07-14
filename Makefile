$(shell touch .env)
include .env
export $(shell sed 's/=.*//' .env)

setup:
	@echo "Setting up environment..."
