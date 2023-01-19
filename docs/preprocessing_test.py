import numpy as np
import time
import tritonclient.grpc as grpcclient

if __name__ == '__main__':
    server_url = 'localhost:8502'
    model_name = "Deeplc_Triton_ensemble"
    out_layers = ['single_ac','peptides_in:0','diamino_ac','general_features']
    batch_size = 1
    inputs = []
    outputs = []

    triton_client = grpcclient.InferenceServerClient(url=server_url)

    inputs.append(grpcclient.InferInput('peptides_in_str:0', [batch_size,1], "BYTES"))

    # Create the data for the two input tensors. Initialize the first
    # to unique integers and the second to all ones.
    peptide_seq_in = np.array([ [b"KK[UNIMOD:37]KKKKK",b"KK[UNIMOD:37]KKKKK"] for i in range (0,batch_size) ], dtype=np.object_)



    
    # Initialize the data
    print("len: "  + str(len(inputs)))
    inputs[0].set_data_from_numpy(peptide_seq_in)
    
    for out_layer in out_layers:
        outputs.append(grpcclient.InferRequestedOutput(out_layer))

    start = time.time()
    result = triton_client.infer(model_name,inputs=inputs, outputs=outputs)
    end = time.time()
    print( "Time: " + str(end - start))   

    print('Result')
    print(result.as_numpy(out_layer))
