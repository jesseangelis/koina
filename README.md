# Koina

## Accessing a public server
### curl
Here is an example http request using only curl sending a POST request to with a json body.

```bash
curl "http://koina.proteomicsdb.org/v2/models/Prosit_2019_intensity/infer" \
 --data-raw '
{
  "id": "LGGNEQVTR_GAGSSEPVTGLDAK",
  "inputs": [
    {"name": "peptide_sequences",   "shape": [2,1], "datatype": "BYTES", "data": ["LGGNEQVTR","GAGSSEPVTGLDAK"]},
    {"name": "collision_energies",  "shape": [2,1], "datatype": "FP32",  "data": [25,25]},
    {"name": "precursor_charges",    "shape": [2,1], "datatype": "INT32", "data": [1,2]}
  ]
}'
```


### Python
See the examples in the corresponding [documentation folder](docs/Python/)

### R
TODO


## Hosting your own server

### Dependencies
dlomix-serving depends on [docker](https://docs.docker.com/engine/install/) and [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/overview.html). 

You can find an ansible script that installs all dependencies [here](docs/server/).

### How to run it
After installing the dependencies you can pull the docker image and run it with. 
```bash
docker run \
    --gpus all \
    --shm-size 2G \
    --name koina \
    -p 8500-8502:8500-8502 \
    -d \
    --restart unless-stopped \
    ghcr.io/wilhelm-lab/koina:latest
```

If you want to stay up to date with the latest version of Koina we suggest you also deploy containrrr/watchtower.

```bash
docker run 
  -d \  
  --name watchtower \   
  -v /var/run/docker.sock:/var/run/docker.sock \  
  containrrr/watchtower -i 30
```

## Adding your own model

### Set up a development server

1. Install dependencies ([Ansible script](docs/server/))
2. (Suggested) Install [docker-compose](https://docs.docker.com/desktop/install/linux-install/)
3. Clone the repo
4. Download existing models with `./getModels.sh`
5. Update `.env` with your user- and group-id to avoid file permission issues 
6. Start the server with `docker-compose up -d`
7. Confirm that the server started successfully with `docker-compose logs -f serving`

Some further considerations:
- For development we suggest to use Visual Studio Code with the `Dev Containers` and `Remote - SSH` extensions.
  Using this system you can connect to the server and open the cloned git repo. You will be prompted to reopen the folder in a Devcontainer where a lot of useful dependencies are already installed including the dependencies required for testing, linting and styling. Using the devcontainer you can lint your code by running `lint`, run all tests with `pytest` and style your code with `black .`
- Server with multiple gpus:
  If you have multiple GPUs in your server and want to use a specific gpu you can specify this in the `docker-comppose.yaml` by replacing `count: 1` with `device_ids: ['1']`

### Import model files
Triton supports all major machine learning frameworks. The format you need to save your model in depends on the framework used to train your model. For detailed instructions you can check out this [documentation](https://github.com/triton-inference-server/server/blob/main/docs/user_guide/model_repository.md#model-files).
You can find examples for [TensorFlow](models/Prosit/Prosit_2019_intensity/1), [PyTorch](models/AlphaPept/AlphaPept_ms2_generic/1) and [XGBoost](models/ms2pip/model_20210416_HCD2021_Y/1) in our model repository. 

#### Model repository
For storing the model files themselves we use Zenodo. If you want to add your model to the publicly available Koina instances, You should upload your model file to Zenodo and commit a file named `.zenodo` containing the download url in place of the real model file.

### Create pre- and post-processing steps
A major aspect of Koina, is that all models share a common interface making it easier for clients to use all models.
Triton supports models written in pure python. If your model requires pre- and/or post-processing you can implement this as a "standalone" model in python.
There are numerous examples in this repository. One with low complexity you can find [here](models/AlphaPept/AlphaPept_Preprocess_charge/1).

### Create an ensemble model to connect everything
The pre- and postprocessing models you just implemented need to be connected to the 
Ensemble models don't have any code themselves they just manage moving tensors between other models. This is perfect for combining your potentially various pre- and post-processing steps with your main model to create one single model/workflow.

### Write tests for your model
To make sure that your model was implemented correctly and future changes do not make any unforseen changes you can add tests for it in the `test` folder. The files added there should match the model name used in the model repository.