from langchain import PromptTemplate
from langchain_core.prompts.chat import MessagePromptTemplateT

# {sentence}
describe_image: MessagePromptTemplateT = PromptTemplate.from_template(
    """
You will be provided with an image from a bioinformatics paper and its corresponding caption. Your task is to generate a short description of the image based on the provided information. Please include the following elements in your description:

Input:
Caption: {caption}
Output:
Generate a detailed description of the image incorporating the five elements listed above.

Example Input:
Image: [Placeholder for a specific bioinformatics paper image, such as a gene expression heatmap]
Caption: "Figure 1 expression levels of various genes under different treatment conditions. Color gradient from red to green represents high to low expression levels."
Example Output:
"Figure 1 is a gene expression heatmap used to compare the expression levels of several genes under different treatment conditions. "
    """
)

explain_plug: MessagePromptTemplateT = PromptTemplate.from_template(
    """
The purpose of this drawing plugin and the files that need to be provided are explained through the following three documents.
ui.json
{ui}

data.json
{data}

meta.json
{meta}

README.md
{readme}

Please specify the data and parameters required for this plugin.
Independently start a new line to explain what data needs to be input and in what order.
    """
)

extract_params: MessagePromptTemplateT = PromptTemplate.from_template(
    """
Help me extract the parameters image_description and image_filepath from the sentence below 
{sentence} 
You only need to return a JSON object.
    """
)

# {json_data}
explain_title: MessagePromptTemplateT = PromptTemplate.from_template(
    """
I have a JSON data structure where 'title' is an array representing the column headers of the data, and 'data' is a two-dimensional array where each one-dimensional array represents a row of data corresponding to the headers. Please help me explain the possible meanings of each header based on the data content. 
{json_data} 
You only need to return a JSON object, where the key represents the header and the value represents the meaning of each header.
    """
)

# {description_json} {input_json}
select_params: MessagePromptTemplateT = PromptTemplate.from_template(
    """
I have two sets of JSON data. The first set contains variable names and their descriptions that can be chosen from, and the second set contains variable names and their descriptions that need to be input. Help me select appropriate values from the first set of data to fill in each object in the second set of data. 
{description_json} 
{input_json} 
You only need to return a JSON object, where the key represents the variable name that needs to be input, and the value represents the chosen variable name used for input.
    """
)

select_extra_params: MessagePromptTemplateT = PromptTemplate.from_template(
    """
Please fill in each extra option in JSON format according to the image, option description and the data top3, so that the options correspond to the features of the image.

The comments for each option and the default values are as follows.You must to adjust the default parameters to meet the given image.
{description}

Optional options for each parameter, the range and meaning are as follows.
{item}

If there are options for data type in options, chose by input.
data_type: {data_type}

You only need to return a JSON object, where the key represents the variable name that needs to be input, and the value represents the chosen variable name used for input.

Example output:
{{
"time_unit": "Year",
"anno_x":0.5
}}
Pay attention to details such as color, and do not output default parameters!
    """
)

# {image_type} {documents}
get_plugin_name: MessagePromptTemplateT = PromptTemplate.from_template(
    """
According to the description below, extract a plugin from the documents that matches the description. If none is found, return None.  
description:  
{image_description}  
documents:  
{documents}  
You only need to return the corresponding original JSON object, without changing case or other details.
    """
)
