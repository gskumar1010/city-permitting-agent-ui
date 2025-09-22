# Mechanic Chatbot for Classic Corvettes Demo

# Architectural Components
- Chatbot
- LLama Stack Backend
- Milvus Vector Database

helm-dev configuration uses a community LLama Stack environment called my-llama-stack, which is wired to OpenAI GPT-4 and an externally hosted Milvus server on db.

helm-prod configuration uses the LLama Stack distribution provided by OpenShift AI, which also provides an embedded Milvus server.  All transactional data is stored on a single PVC for this demo.

# Installation (helm-prod)

## Deploy LLM for use with LLama Stack and by the Application

It is assumed that everything is colocated in a single project.

1. Create an OpenShift AI Project for the application.  i.e. Mechanic
2. Deploy an LLM to be used by the application. 

Example - LLama 3.2 3b Instruct (Red Hat OpenShift AI's reference documentation default)

            - Model name: llama32
            - Serving runtime: vLLM NVIDIA GPU ServingRuntime for KServe
            - Deployment mode: Standard
            - Number of replicas: 1
            - Hardware profile: NVIDIA GPU
            - Customized resource limits:  CPU: Request = 1; Limit = 1; Memory: Request = 4Gi; Limit = 4Gi; nvidia.com/gpu: Request = 1; Limit = 1
            - Model route: Make deployed models available externally
            - Token authentication: Require token authentication
            - Source model location: URI
            - URI: oci://quay.io/redhat-ai-services/modelcar-catalog:llama-3.2-3b-instruct
            - Additional serving runtime arguments:
            --dtype=half
            --max-model-len=20000
            --gpu-memory-utilization=0.95
            --enable-chunked-prefill
            --enable-auto-tool-choice
            --tool-call-parser=llama3_json
            --chat-template=/app/data/template/tool_chat_template_llama3.2_json.jinja

Example - LLama 3.3 70b Instruct (H200)

            - Model name: llama33
            - Serving runtime: vLLM NVIDIA GPU ServingRuntime for KServe
            - Deployment mode: Standard
            - Number of replicas: 1
            - Hardware profile: NVIDIA GPU
            - Customized resource limits:  CPU: Request = 2; Limit = 4; Memory: Request = 4Gi; Limit = 8Gi; nvidia.com/gpu: Request = 1; Limit = 1
            - Model route: Make deployed models available externally
            - Token authentication: Require token authentication
            - Source model location: URI
            - URI: oci://registry.redhat.io/rhelai1/modelcar-llama-3-3-70b-instruct-fp8-dynamic:1.5
            - Additional serving runtime arguments:
            --max-model-len=16384
            --enable-chunked-prefill
            --enable-auto-tool-choice
            --tool-call-parser=llama3_json
            
Example - LLama 3.3 70b Instruct (H100)

            - Model name: llama33
            - Serving runtime: vLLM NVIDIA GPU ServingRuntime for KServe
            - Deployment mode: Standard
            - Number of replicas: 1
            - Hardware profile: NVIDIA GPU
            - Customized resource limits:  CPU: Request = 2; Limit = 4; Memory: Request = 4Gi; Limit = 8Gi; nvidia.com/gpu: Request = 1; Limit = 1
            - Model route: Make deployed models available externally
            - Token authentication: Require token authentication
            - Source model location: URI
            - URI: oci://registry.redhat.io/rhelai1/modelcar-llama-3-3-70b-instruct-quantized-w4a16:1.5
            - Additional serving runtime arguments:
            --max-model-len=16384
            --enable-chunked-prefill
            --enable-auto-tool-choice
            --tool-call-parser=llama3_json

## LLama Stack with OpenShift AI

1. The LLama Stack operator must be enabled in the DSC YAML in the OpenShift AI operator.
2. Connect to the cluster from the CLI using the Copy Login Command in the upper right hand side of the OpenShift Console.
3. Change to the project that was just created above.

            oc project mechanic

4. In this GitHub project under deploy/ocp, secret.txt contains environment variables and a command needed to create the secret needed for the LLS distroy.  Change the environment variables to match this environment and then run the create secret command.

            more deploy/ocp/secret.txt

5. Create the LLama Stack operator instance using the YAML in the same folder as the secret.txt file.

            oc apply -f llama_stack_operator_instance.yaml

6. Wait for the LLama Stack distribution to startup.

            watch -n 1 oc get pods --namespace mechanic

7. [optional] If you want to test against the remote LLS distribution or plan to do the data ingestion remote, create a route for it using lls_route.yaml in same folder.

            oc apply -f lls_route.yaml

## Ingest Data

Milvus must be hydrated with content before the chatbot will be functional.  This is currently orchestrated through make with the Makefile in the root directory.

1. Change LLAMA_STACK_URL to map to the LLama Stack route provided above.  If done from the context of a workbench, the internal service URL can be used instead of making the environment available externally.
2. Change MODEL to the name of the model that you wish to leverage through the LLama Stack runtime.
3. Change EMBEDDING_MODEL to the embedding model you wish to use for vectorized content through the LLama Stack runtime.
4. Run make ingest-data.  This will take several minutes.

            make ingest-data

## Deploy Chatbot

1. Checkout this project to your local filesystem.

            git clone https://github.com/glroland/mechanic.git

2. From a command line, change to mechanic folder, then to the deploy/helm-prod sub folder.

            cd mechanic/deploy/helm-prod

3. Assumed that helm is installed and you are still connected to the OpenShift cluster referred to above.
4. Change to the mechanic namespace

            oc project mechanic

5. Install the application through helm.

            helm install m1 .

6. Wait for the application to startup.

            watch -n 1 oc get pods --namespace mechanic

## Health Check / Test Steps

1. Get the Chatbot URL

            oc get routes -n mechanic | grep chatbot

2. Open the application in your web browser
3. Paste the following into the message bar at the bottom of the screen.

            What changes were made to the 1972 model year?

4. The system is working as expected if the answer to the first question is something like this:

> Based on the provided knowledge, the 1972 Corvette model year saw very few changes. The main change was the introduction of a new rating system that uses net horsepower instead of gross power outputs, which resulted in a decrease in rated horsepower. Additionally, the audio alarm antitheft system was not a standard item, and the fiber optic light monitors were discontinued. The body style remained the same, with only three engine options available: two 350 cubic inch engines and one 454 cubic inch engine.

# Representative Questions

- Example 1

            What do the identification numbers stamped on the engine block mean for the 72 model year?

- Example 2
  
            What are possible causes for a slow engine crank?

- Example 3

            What are the steps to drain and refill the cooling system?
