import os
import logging
import json
import io
import urllib.parse
import urllib.request
import requests
from mcp.server.fastmcp import FastMCP
import uvicorn
from docling.backend.html_backend import HTMLDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument
from mrkdwn_analysis import MarkdownAnalyzer

# configurable parameters
ENV_MCP_PORT = "MCP_PORT"
ENV_LOG_LEVEL = "LOG_LEVEL"
ENV_GCP_API_KEY = "GCP_API_KEY"
ENV_GOOGLE_CX = "GOOGLE_CX"

# Constants
SEARCH_URL = "https://customsearch.googleapis.com/customsearch/v1"
SEARCH_PARAM_KEY = "key"
SEARCH_PARAM_CX = "cx"
SEARCH_PARAM_QUERY = "q"

# Headers
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# setup MCP server
mcp_port = 8080
if ENV_MCP_PORT in os.environ:
    mcp_port = int(os.environ[ENV_MCP_PORT])
logger.info("MCP Port: %s", mcp_port)

# Retrieve config
if ENV_GCP_API_KEY not in os.environ:
    msg = "'GCP_API_KEY' is required and has not been set!"
    logger.fatal(msg)
    raise ValueError(msg)
gcp_api_key = os.environ[ENV_GCP_API_KEY]
if ENV_GOOGLE_CX not in os.environ:
    msg = "'GOOGLE_CX' is required and has not been set!"
    logger.fatal(msg)
    raise ValueError(msg)
google_cx = os.environ[ENV_GOOGLE_CX]

# Start MCP Server
mcp = FastMCP(name="Corvette Forum MCP Server")

@mcp.tool(
    annotations={
        "title": "Search Corvette Forum's C3 Corvette Tech Support Website",
        "readOnlyHint": True,
        "openWorldHint": True,
    }
)
def search_c3_tech_support(query: str) -> str:
    """ Search's Corvette Forum's online community for C3 performance and tech support.

    :param query: Search Query
    :returns: Search results
    """
    logger.info ("Searching C3 Tech Support.  Query=%s", query)

    # validate parameters
    if query is None or len(query) == 0:
        msg = "Query is required but is empty!"
        logger.error(msg)
        raise ValueError(msg)

    # build url
    query_parameters = {
        SEARCH_PARAM_KEY: gcp_api_key,
        SEARCH_PARAM_CX: google_cx,
        SEARCH_PARAM_QUERY: query,
    }
    url = SEARCH_URL + "?" + urllib.parse.urlencode(query_parameters)

    # make get request
    response = requests.get(url)
    if response.status_code != 200:
        msg = "Unable to perform search.  HTTP Status Code = " + response.status_code
        logger.erorr(msg)
        raise ValueError(msg)

    # process results
    search_results = response.json()
    pretty_json = json.dumps(search_results, indent=4)
    logger.debug("Search Results for query (%s) == %s", query, pretty_json)
 
    # extract meaningful content
    matching_content = []
    for item in search_results["items"]:
        link = item["link"]
        snippet = item["snippet"]

        content = {"link": link,
                   "snippet": snippet}
        
        matching_content.append(content)
    logger.info("# of Matches Found for Query:  Count=%s. Query=%s", len(matching_content), query)
    logger.debug("Matching Content:  Count=%s  Items=%s", len(matching_content), matching_content)

    # setup information extraction
    for content in matching_content:
        if content == matching_content[0]:
            # download page content
            url = content["link"]
            logger.info("Download forum content for url: %s", url)
            request = urllib.request.Request(url, headers=HEADERS)
            page_contents = urllib.request.urlopen(request).read()

            # convert html to markdown
            logger.info("Converting page contents to markdown")
            page_contents_stream = io.BytesIO(page_contents)
            input_doc = InputDocument(
                path_or_stream=page_contents_stream,
                format=InputFormat.HTML,
                backend=HTMLDocumentBackend,
                filename="does_not_matter.html",
            )
            backend = HTMLDocumentBackend(in_doc=input_doc, path_or_stream=page_contents_stream)
            doc_result = backend.convert()
            markdown = doc_result.export_to_markdown()
            #content["md"] = markdown

            print (markdown)

            # filter by section
            md_analyzer = MarkdownAnalyzer.from_string(markdown)
            headers = md_analyzer.identify_headers()
            logger.info("Headers in Markdown: %s", headers)
            print(headers)




    return matching_content


sse_app = mcp.sse_app()

@sse_app.route("/health")
async def health_check(request):
    """ Health check endpoint for the MCP Server. """
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    port = 8080
    if ENV_MCP_PORT in os.environ:
        port = int(os.environ[ENV_MCP_PORT])
    print ("Port: ", port)

    print ("Testing search_c3_tech_support...")
    print (search_c3_tech_support(query="lights"))
    print ()

    log_level = "info"
    if ENV_LOG_LEVEL in os.environ:
        log_level = os.environ[ENV_LOG_LEVEL]
    print ("Log Level: ", log_level)

    print ("Starting MCP Server...")
    uvicorn.run(sse_app, host="0.0.0.0", port=port, log_level=log_level)
