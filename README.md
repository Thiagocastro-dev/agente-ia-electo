## Ambiente de testes

O teste unitário não depende de serviços externos:

```bash
uv sync
uv run pytest
```

Para testes de integração, copie a configuração de teste e suba PostgreSQL e Qdrant em portas e volumes separados do ambiente normal:

```bash
cp .env.test.example .env.test
make test-infra-up
set -a; source .env.test; set +a
uv run pytest
make test-infra-down
```

O PostgreSQL de teste usa o banco `rag_test` na porta `55432`, e o Qdrant usa a porta `56333`. Os dados ficam em volumes Docker nomeados e não compartilham o armazenamento de desenvolvimento.
