#!/usr/bin/python3
import logging
import os
import json
import time
from pathlib import Path
import html
import yaml
import requests
from jinja2 import Environment, FileSystemLoader

nptype_convert = {
    "FP32": "np.float32",
    "BYTES": "np.object_",
    "INT32": "np.int32",
    "INT64": "np.int64",
}


def load_yaml(path):
    with open(path, "r", encoding="UTF-8") as yaml_file:
        return yaml.load(yaml_file, Loader=yaml.FullLoader)


def generate_example_code(model, grpc_url):
    """
    Generates the GRPC examples codes based on the notes
    """
    python_code_template = "swagger/templates/python_code.txt"
    logging.info(f"Using grpc url:\t{grpc_url}")
    logging.info(f"Using template to create python code:\t\t{python_code_template}")
    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template(python_code_template)
    context = model
    context["url"] = grpc_url

    txt = html.escape(template.render(context)).replace("\n", "<br>")
    return f"<pre>{txt}</pre>"


def sleep_until_service_starts(http_server):
    serving_started = False
    wait_time = 10

    url = f"{http_server}/v2/health/ready"
    while not serving_started:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code >= 200 and r.status_code <= 299:
                serving_started = True
                logging.info("Serving started continuing the program")
                return
            logging.info(f"Waiting for serving to start: {url}")
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError:
            logging.info(f"Waiting for serving to start: {url}")
            time.sleep(wait_time)


def get_config(http_url, name):
    url = http_url + f"/v2/models/{name}/config"
    logging.info(f"Getting config from:\t\t{url}")
    r = requests.get(url, timeout=1)
    return r.json()


def create_swagger_yaml(models, tmpl_url):
    # Create the Swagger.yaml based on the template

    swagger_template_file = "swagger/templates/swagger.yml"
    logging.info(f"Using template file:\t\t{swagger_template_file}")

    environment = Environment(loader=FileSystemLoader("./"))
    template = environment.get_template(swagger_template_file)
    context = {"models": models, "tmpl_url": tmpl_url}

    content = template.render(context)
    with open("swagger/swagger.yml", mode="w", encoding="utf-8") as yam:
        yam.write(content)
    logging.info("Finished Generating the Swagger YAML file.")


def main(http_url, grpc_url, tmpl_url):
    model_dict = {x.parent.name: x for x in Path("models").rglob("notes.yaml")}

    # there is a slight delay before service turns healthy
    # therefore sleep just a few seconds
    sleep_until_service_starts(http_url)

    # models = get_configs(model_dict.keys())
    # logging.info(f"Models: {models}")

    # Remove the type prefix because the python code doesn't use the same type notations
    # models = remove_type_prefix(models)

    models = []
    for name, model_path in model_dict.items():
        logging.info(f"Start working on model:\t{name}")
        models.append(
            {
                "name": name,
                "note": load_yaml(model_path),
                "config": get_config(http_url, name),
            }
        )
        add_np_and_swagger_dtype(models[-1]["note"])
        copy_outputs_to_note(models[-1])
        verify_inputs(models[-1])
        models[-1]["code"] = generate_example_code(models[-1], grpc_url)

    logging.info(f"Template URL: {tmpl_url}")
    create_swagger_yaml(models, tmpl_url)


def copy_outputs_to_note(model_dict):
    model_dict["note"]["outputs"] = [o["name"] for o in model_dict["config"]["output"]]


def verify_inputs(model_dict):
    for x, y in zip(
        model_dict["note"]["examples"]["inputs"], model_dict["config"]["input"]
    ):
        try:
            assert x["name"] == y["name"]
            assert x["httpdtype"] == tritondtype_to_httpdtype(y["data_type"])
        except AssertionError:
            raise AssertionError(
                f"Inputs inconsistent for {model_dict['name']} {x} != {y}"
            )


def httpdtype_to_npdtype(dtype):
    mapping = {
        "FP32": 'np.dtype("float32")',
        "BYTES": 'np.dtype("O")',
        "INT16": 'np.dtype("int16")',
        "INT32": 'np.dtype("int32")',
        "INT64": 'np.dtype("int64")',
    }
    return mapping[dtype]


def httpdtype_to_swaggerdtype(dtype):
    if dtype == "BYTES":
        return "string"
    return "number"


def tritondtype_to_httpdtype(dtype):
    if dtype == "TYPE_STRING":
        return "BYTES"
    return dtype.replace("TYPE_", "")


def add_np_and_swagger_dtype(model_note):
    for x in model_note["examples"]["inputs"]:
        x["npdtype"] = httpdtype_to_npdtype(x["httpdtype"])
        x["swaggerdtype"] = httpdtype_to_swaggerdtype(x["httpdtype"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    config = load_yaml("swagger/config.yml")
    main(config["HTTP_URL"], config["TMPLT_GRPC_URL"], config["TMPLT_HTTP_URL"])
