import typer 
from typing import Annotated

from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import classic_load_key

from prediction.validator._config import ValidatorSettings
from prediction.validator.validation import get_subnet_netuid, Validation
import asyncio

app = typer.Typer()


@app.command("serve-subnet")
def serve(
    commune_key: Annotated[
        str, typer.Argument(help="Name of the key present in `~/.commune/key`")
    ],
    call_timeout: int = 60,
):
    keypair = classic_load_key(commune_key)
    settings = ValidatorSettings()
    client = CommuneClient(get_node_url())
    subnet_uid = get_subnet_netuid(client, "prediction")
    print(f"subnet_uid: {subnet_uid}")
    validator = Validation(
        keypair,
        subnet_uid,
        client,
        call_timeout=call_timeout,
    )
    
    asyncio.run(validator.validation_loop(settings))


if __name__ == "__main__":
    typer.run(serve)
