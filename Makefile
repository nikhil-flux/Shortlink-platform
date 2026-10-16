.PHONY: test up down k8s-up k8s-down

test:
	pip install -q -r requirements-dev.txt && pytest -q

up:
	docker compose up --build -d

down:
	docker compose down -v

k8s-up:
	kubectl apply -k k8s/overlays/dev

k8s-down:
	kubectl delete -k k8s/overlays/dev
