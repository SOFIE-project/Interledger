import pytest

# def pytest_addoption(parser):
#     parser.addoption(
#         "--config", action="store", help="configuration file path"
#     )


# @pytest.fixture
# def config(request):
#     return request.config.getoption("--config")

@pytest.fixture
def config():
    return "local-config.cfg"
