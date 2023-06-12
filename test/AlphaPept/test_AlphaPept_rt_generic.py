from test.server_config import SERVER_GRPC, SERVER_HTTP
import tritonclient.grpc as grpcclient
import numpy as np
import requests
from pathlib import Path


# To ensure MODEL_NAME == test_<filename>.py
MODEL_NAME = Path(__file__).stem.replace("test_", "")


def test_available_http():
    req = requests.get(f"{SERVER_HTTP}/v2/models/{MODEL_NAME}", timeout=1)
    assert req.status_code == 200


def test_available_grpc():
    triton_client = grpcclient.InferenceServerClient(url=SERVER_GRPC)
    assert triton_client.is_model_ready(MODEL_NAME)


def test_inference():
    SEQUENCES = np.array(
        [
            ["LGGNEQVTR"],
            ["GAGSSEPVTGLDAK"],
            ["VEATFGVDESNAK"],
            ["YILAGVENSK"],
            ["TPVISGGPYEYR"],
            ["TPVITGAPYEYR"],
            ["DGLDAASYYAPVR"],
            ["ADVTPADFSEWSK"],
            ["GTFIIDPGGVIR"],
            ["GTFIIDPAAVIR"],
            ["LFLQFGAQGSPFLK"],
        ],
        dtype=np.object_,
    )

    triton_client = grpcclient.InferenceServerClient(url=SERVER_GRPC)

    in_pep_seq = grpcclient.InferInput("peptide_sequences", SEQUENCES.shape, "BYTES")
    in_pep_seq.set_data_from_numpy(SEQUENCES)

    result = triton_client.infer(
        MODEL_NAME,
        inputs=[in_pep_seq],
        outputs=[
            grpcclient.InferRequestedOutput("irt"),
        ],
    )

    irt = result.as_numpy("irt")

    assert irt.shape == (11, 1)

    # Assert intensities consistent
    assert np.allclose(
        irt,
        np.load("test/AlphaPept/arr_AlphaPept_irt_mb.npy").reshape(-1, 1),
        rtol=0,
        atol=1e-4,
    )
