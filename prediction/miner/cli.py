import typer 
from typing import Annotated, Optional

from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key
from communex.module._rate_limiters.limiters import StakeLimiterParams
from communex.module.server import ModuleServer

from prediction.validator._config import ValidatorSettings
from prediction.validator.validation import get_subnet_netuid, Validation

from prediction.miner.app import Miner
import uvicorn

app = typer.Typer()


@app.command("serve-miner")
def serve(
    commune_key: Annotated[
        str, typer.Argument(help="Name of the key present in `~/.commune/key`")
    ],
    ip: Optional[str] = None,
    port: Optional[int] = None,
):
    keypair = classic_load_key(commune_key)
    module = Miner()
        
    server = ModuleServer(
        module, keypair, subnets_whitelist=[9]
    )
    
    miner_app = server.get_fastapi_app()
    host = ip or "127.0.0.1"
    port_ = port or 8000
    uvicorn.run(miner_app, host=host, port=port_)


if __name__ == "__main__":
    typer.run(serve)
