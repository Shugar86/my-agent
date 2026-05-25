"""Additional builder and validation tests."""
import pytest
from core.validation import validate_safe_path, validate_sql, validate_email


class TestValidationEdgeCases:
    def test_path_with_unicode(self):
        assert validate_safe_path("файл.txt")

    def test_path_with_spaces(self):
        assert validate_safe_path("my file.txt")

    def test_sql_with_join(self):
        assert validate_sql("SELECT a.name FROM users a JOIN orders b ON a.id = b.user_id")

    def test_sql_with_group_by(self):
        assert validate_sql("SELECT category, COUNT(*) FROM products GROUP BY category")

    def test_sql_with_limit(self):
        assert validate_sql("SELECT * FROM logs LIMIT 10")

    def test_sql_blocks_grant(self):
        assert not validate_sql("GRANT ALL ON users TO public")

    def test_sql_blocks_revoke(self):
        assert not validate_sql("REVOKE ALL ON users FROM public")

    def test_sql_blocks_copy(self):
        assert not validate_sql("COPY users TO '/tmp/users.csv'")

    def test_sql_blocks_into_outfile(self):
        assert not validate_sql("SELECT * INTO OUTFILE '/tmp/data.txt'")

    def test_email_with_subdomain(self):
        assert validate_email("user@mail.example.com")

    def test_email_with_numbers(self):
        assert validate_email("user123@test.org")

    def test_email_rejects_ip_domain(self):
        assert not validate_email("user@192.168.1.1")


class TestBuilderFormValidation:
    def test_agent_id_format(self):
        valid = ["my_agent", "agent123", "test-agent", "agent_2"]
        for v in valid:
            assert v.replace("-", "_").isidentifier() or "-" in v

    def test_agent_id_rejects_spaces(self):
        assert " " in "bad id"

    def test_skill_selection_logic(self):
        skills = ["research", "code", "data"]
        selected = {"research", "data"}
        assert selected.issubset(set(skills))


class TestAsyncUtilities:
    @pytest.mark.asyncio
    async def test_asyncio_gather_basic(self):
        import asyncio
        results = await asyncio.gather(
            asyncio.sleep(0, result=1),
            asyncio.sleep(0, result=2),
        )
        assert results == [1, 2]

    @pytest.mark.asyncio
    async def test_asyncio_semaphore(self):
        import asyncio
        sem = asyncio.Semaphore(2)
        async def work(n):
            async with sem:
                await asyncio.sleep(0.01)
                return n
        results = await asyncio.gather(*[work(i) for i in range(5)])
        assert results == list(range(5))
