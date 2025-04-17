Gemini
Install
To use GeminiModel models, you just need to install pydantic-ai or pydantic-ai-slim, no extra dependencies are required.

Configuration
GeminiModel let's you use the Google's Gemini models through their Generative Language API, generativelanguage.googleapis.com.

GeminiModelName contains a list of available Gemini models that can be used through this interface.

To use GeminiModel, go to aistudio.google.com and select "Create API key".

Environment variable
Once you have the API key, you can set it as an environment variable:


export GEMINI_API_KEY=your-api-key
You can then use GeminiModel by name:

gemini_model_by_name.py

from pydantic_ai import Agent

agent = Agent('google-gla:gemini-2.0-flash')
...
Note

The google-gla provider prefix represents the Google Generative Language API for GeminiModels. google-vertex is used with Vertex AI.

Or initialise the model directly with just the model name and provider:

gemini_model_init.py

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel

model = GeminiModel('gemini-2.0-flash', provider='google-gla')
agent = Agent(model)
...
provider argument
You can provide a custom Provider via the provider argument:

gemini_model_provider.py

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

model = GeminiModel(
    'gemini-2.0-flash', provider=GoogleGLAProvider(api_key='your-api-key')
)
agent = Agent(model)
...
You can also customize the GoogleGLAProvider with a custom http_client:
gemini_model_custom_provider.py

from httpx import AsyncClient

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

custom_http_client = AsyncClient(timeout=30)
model = GeminiModel(
    'gemini-2.0-flash',
    provider=GoogleGLAProvider(api_key='your-api-key', http_client=custom_http_client),
)
agent = Agent(model)
...

Function Tools vs. Structured Results
As the name suggests, function tools use the model's "tools" or "functions" API to let the model know what is available to call. Tools or functions are also used to define the schema(s) for structured responses, thus a model might have access to many tools, some of which call function tools while others end the run and return a result.

Function tools and schema
Function parameters are extracted from the function signature, and all parameters except RunContext are used to build the schema for that tool call.

Even better, PydanticAI extracts the docstring from functions and (thanks to griffe) extracts parameter descriptions from the docstring and adds them to the schema.

Griffe supports extracting parameter descriptions from google, numpy, and sphinx style docstrings. PydanticAI will infer the format to use based on the docstring, but you can explicitly set it using docstring_format. You can also enforce parameter requirements by setting require_parameter_descriptions=True. This will raise a UserError if a parameter description is missing.

To demonstrate a tool's schema, here we use FunctionModel to print the schema a model would receive:

tool_schema.py

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

agent = Agent()


@agent.tool_plain(docstring_format='google', require_parameter_descriptions=True)
def foobar(a: int, b: str, c: dict[str, list[float]]) -> str:
    """Get me foobar.

    Args:
        a: apple pie
        b: banana cake
        c: carrot smoothie
    """
    return f'{a} {b} {c}'


def print_schema(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    tool = info.function_tools[0]
    print(tool.description)
    #> Get me foobar.
    print(tool.parameters_json_schema)
    """
    {
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'apple pie', 'type': 'integer'},
            'b': {'description': 'banana cake', 'type': 'string'},
            'c': {
                'additionalProperties': {'items': {'type': 'number'}, 'type': 'array'},
                'description': 'carrot smoothie',
                'type': 'object',
            },
        },
        'required': ['a', 'b', 'c'],
        'type': 'object',
    }
    """
    return ModelResponse(parts=[TextPart('foobar')])


agent.run_sync('hello', model=FunctionModel(print_schema))
(This example is complete, it can be run "as is")

The return type of tool can be anything which Pydantic can serialize to JSON as some models (e.g. Gemini) support semi-structured return values, some expect text (OpenAI) but seem to be just as good at extracting meaning from the data. If a Python object is returned and the model expects a string, the value will be serialized to JSON.

If a tool has a single parameter that can be represented as an object in JSON schema (e.g. dataclass, TypedDict, pydantic model), the schema for the tool is simplified to be just that object.

Here's an example where we use TestModel.last_model_request_parameters to inspect the tool schema that would be passed to the model.

single_parameter_tool.py

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

agent = Agent()


class Foobar(BaseModel):
    """This is a Foobar"""

    x: int
    y: str
    z: float = 3.14


@agent.tool_plain
def foobar(f: Foobar) -> str:
    return str(f)


test_model = TestModel()
result = agent.run_sync('hello', model=test_model)
print(result.data)
#> {"foobar":"x=0 y='a' z=3.14"}
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='foobar',
        description='This is a Foobar',
        parameters_json_schema={
            'properties': {
                'x': {'type': 'integer'},
                'y': {'type': 'string'},
                'z': {'default': 3.14, 'type': 'number'},
            },
            'required': ['x', 'y'],
            'title': 'Foobar',
            'type': 'object',
        },
        outer_typed_dict_key=None,
    )
]
"""
(This example is complete, it can be run "as is")

Dynamic Function tools
Tools can optionally be defined with another function: prepare, which is called at each step of a run to customize the definition of the tool passed to the model, or omit the tool completely from that step.

A prepare method can be registered via the prepare kwarg to any of the tool registration mechanisms:

@agent.tool decorator
@agent.tool_plain decorator
Tool dataclass
The prepare method, should be of type ToolPrepareFunc, a function which takes RunContext and a pre-built ToolDefinition, and should either return that ToolDefinition with or without modifying it, return a new ToolDefinition, or return None to indicate this tools should not be registered for that step.

Here's a simple prepare method that only includes the tool if the value of the dependency is 42.

As with the previous example, we use TestModel to demonstrate the behavior without calling a real model.

tool_only_if_42.py

from typing import Union

from pydantic_ai import Agent, RunContext
from pydantic_ai.tools import ToolDefinition

agent = Agent('test')


async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> Union[ToolDefinition, None]:
    if ctx.deps == 42:
        return tool_def


@agent.tool(prepare=only_if_42)
def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'


result = agent.run_sync('testing...', deps=41)
print(result.data)
#> success (no tool calls)
result = agent.run_sync('testing...', deps=42)
print(result.data)
#> {"hitchhiker":"42 a"}
(This example is complete, it can be run "as is")

Here's a more complex example where we change the description of the name parameter to based on the value of deps

For the sake of variation, we create this tool using the Tool dataclass.

customize_name.py

from __future__ import annotations

from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.tools import Tool, ToolDefinition


def greet(name: str) -> str:
    return f'hello {name}'


async def prepare_greet(
    ctx: RunContext[Literal['human', 'machine']], tool_def: ToolDefinition
) -> ToolDefinition | None:
    d = f'Name of the {ctx.deps} to greet.'
    tool_def.parameters_json_schema['properties']['name']['description'] = d
    return tool_def


greet_tool = Tool(greet, prepare=prepare_greet)
test_model = TestModel()
agent = Agent(test_model, tools=[greet_tool], deps_type=Literal['human', 'machine'])

result = agent.run_sync('testing...', deps='human')
print(result.data)
#> {"greet":"hello a"}
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='greet',
        description='',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {
                'name': {'type': 'string', 'description': 'Name of the human to greet.'}
            },
            'required': ['name'],
            'type': 'object',
        },
        outer_typed_dict_key=None,
    )
]
"""
(This example is complete, it can be run "as is")

pydantic_ai.result
ResultDataT module-attribute

ResultDataT = TypeVar(
    "ResultDataT", default=str, covariant=True
)
Covariant type variable for the result data type of a run.

StreamedRunResult dataclass
Bases: Generic[AgentDepsT, ResultDataT]

Result of a streamed run that returns structured data via a tool call.

Source code in pydantic_ai_slim/pydantic_ai/result.py
is_complete class-attribute instance-attribute

is_complete: bool = field(default=False, init=False)
Whether the stream has all been received.

This is set to True when one of stream, stream_text, stream_structured or get_data completes.

all_messages

all_messages(
    *, result_tool_return_content: str | None = None
) -> list[ModelMessage]
Return the history of _messages.

Parameters:

Name	Type	Description	Default
result_tool_return_content	str | None	The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the result tool call if you want to continue the conversation and want to set the response to the result tool call. If None, the last message will not be modified.	None
Returns:

Type	Description
list[ModelMessage]	List of messages.
Source code in pydantic_ai_slim/pydantic_ai/result.py
all_messages_json

all_messages_json(
    *, result_tool_return_content: str | None = None
) -> bytes
Return all messages from all_messages as JSON bytes.

Parameters:

Name	Type	Description	Default
result_tool_return_content	str | None	The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the result tool call if you want to continue the conversation and want to set the response to the result tool call. If None, the last message will not be modified.	None
Returns:

Type	Description
bytes	JSON bytes representing the messages.
Source code in pydantic_ai_slim/pydantic_ai/result.py
new_messages

new_messages(
    *, result_tool_return_content: str | None = None
) -> list[ModelMessage]
Return new messages associated with this run.

Messages from older runs are excluded.

Parameters:

Name	Type	Description	Default
result_tool_return_content	str | None	The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the result tool call if you want to continue the conversation and want to set the response to the result tool call. If None, the last message will not be modified.	None
Returns:

Type	Description
list[ModelMessage]	List of new messages.
Source code in pydantic_ai_slim/pydantic_ai/result.py
new_messages_json

new_messages_json(
    *, result_tool_return_content: str | None = None
) -> bytes
Return new messages from new_messages as JSON bytes.

Parameters:

Name	Type	Description	Default
result_tool_return_content	str | None	The return content of the tool call to set in the last message. This provides a convenient way to modify the content of the result tool call if you want to continue the conversation and want to set the response to the result tool call. If None, the last message will not be modified.	None
Returns:

Type	Description
bytes	JSON bytes representing the new messages.
Source code in pydantic_ai_slim/pydantic_ai/result.py

def new_messages_json(self, *, result_tool_return_content: str | None = None) -> bytes:
    """Return new messages from [`new_messages`][pydantic_ai.result.StreamedRunResult.new_messages] as JSON bytes.

    Args:
        result_tool_return_content: The return content of the tool call to set in the last message.
            This provides a convenient way to modify the content of the result tool call if you want to continue
            the conversation and want to set the response to the result tool call. If `None`, the last message will
            not be modified.

    Returns:
        JSON bytes representing the new messages.
    """
    return _messages.ModelMessagesTypeAdapter.dump_json(
        self.new_messages(result_tool_return_content=result_tool_return_content)
    )
stream async

stream(
    *, debounce_by: float | None = 0.1
) -> AsyncIterator[ResultDataT]
Stream the response as an async iterable.

The pydantic validator for structured data will be called in partial mode on each iteration.

Parameters:

Name	Type	Description	Default
debounce_by	float | None	by how much (if at all) to debounce/group the response chunks by. None means no debouncing. Debouncing is particularly important for long structured responses to reduce the overhead of performing validation as each token is received.	0.1
Returns:

Type	Description
AsyncIterator[ResultDataT]	An async iterable of the response data.
Source code in pydantic_ai_slim/pydantic_ai/result.py
stream_text async

stream_text(
    *, delta: bool = False, debounce_by: float | None = 0.1
) -> AsyncIterator[str]
Stream the text result as an async iterable.

Note

Result validators will NOT be called on the text result if delta=True.

Parameters:

Name	Type	Description	Default
delta	bool	if True, yield each chunk of text as it is received, if False (default), yield the full text up to the current point.	False
debounce_by	float | None	by how much (if at all) to debounce/group the response chunks by. None means no debouncing. Debouncing is particularly important for long structured responses to reduce the overhead of performing validation as each token is received.	0.1
Source code in pydantic_ai_slim/pydantic_ai/result.py

async def stream_text(self, *, delta: bool = False, debounce_by: float | None = 0.1) -> AsyncIterator[str]:
    """Stream the text result as an async iterable.

    !!! note
        Result validators will NOT be called on the text result if `delta=True`.

    Args:
        delta: if `True`, yield each chunk of text as it is received, if `False` (default), yield the full text
            up to the current point.
        debounce_by: by how much (if at all) to debounce/group the response chunks by. `None` means no debouncing.
            Debouncing is particularly important for long structured responses to reduce the overhead of
            performing validation as each token is received.
    """
    if self._result_schema and not self._result_schema.allow_text_result:
        raise exceptions.UserError('stream_text() can only be used with text responses')

    if delta:
        async for text in self._stream_response_text(delta=delta, debounce_by=debounce_by):
            yield text
    else:
        async for text in self._stream_response_text(delta=delta, debounce_by=debounce_by):
            combined_validated_text = await self._validate_text_result(text)
            yield combined_validated_text
    await self._marked_completed(self._stream_response.get())
stream_structured async

stream_structured(
    *, debounce_by: float | None = 0.1
) -> AsyncIterator[tuple[ModelResponse, bool]]
Stream the response as an async iterable of Structured LLM Messages.

Parameters:

Name	Type	Description	Default
debounce_by	float | None	by how much (if at all) to debounce/group the response chunks by. None means no debouncing. Debouncing is particularly important for long structured responses to reduce the overhead of performing validation as each token is received.	0.1
Returns:

Type	Description
AsyncIterator[tuple[ModelResponse, bool]]	An async iterable of the structured response message and whether that is the last message.
Source code in pydantic_ai_slim/pydantic_ai/result.py

async def stream_structured(
    self, *, debounce_by: float | None = 0.1
) -> AsyncIterator[tuple[_messages.ModelResponse, bool]]:
    """Stream the response as an async iterable of Structured LLM Messages.

    Args:
        debounce_by: by how much (if at all) to debounce/group the response chunks by. `None` means no debouncing.
            Debouncing is particularly important for long structured responses to reduce the overhead of
            performing validation as each token is received.

    Returns:
        An async iterable of the structured response message and whether that is the last message.
    """
    # if the message currently has any parts with content, yield before streaming
    msg = self._stream_response.get()
    for part in msg.parts:
        if part.has_content():
            yield msg, False
            break

    async for msg in self._stream_response_structured(debounce_by=debounce_by):
        yield msg, False

    msg = self._stream_response.get()
    yield msg, True

    await self._marked_completed(msg)
get_data async

get_data() -> ResultDataT
Stream the whole response, validate and return it.

Source code in pydantic_ai_slim/pydantic_ai/result.py

async def get_data(self) -> ResultDataT:
    """Stream the whole response, validate and return it."""
    usage_checking_stream = _get_usage_checking_stream_response(
        self._stream_response, self._usage_limits, self.usage
    )

    async for _ in usage_checking_stream:
        pass
    message = self._stream_response.get()
    await self._marked_completed(message)
    return await self.validate_structured_result(message)
usage

usage() -> Usage
Return the usage of the whole run.

Note

This won't return the full usage until the stream is finished.

Source code in pydantic_ai_slim/pydantic_ai/result.py

def usage(self) -> Usage:
    """Return the usage of the whole run.

    !!! note
        This won't return the full usage until the stream is finished.
    """
    return self._initial_run_ctx_usage + self._stream_response.usage()
timestamp

timestamp() -> datetime
Get the timestamp of the response.

Source code in pydantic_ai_slim/pydantic_ai/result.py

def timestamp(self) -> datetime:
    """Get the timestamp of the response."""
    return self._stream_response.timestamp
validate_structured_result async

validate_structured_result(
    message: ModelResponse, *, allow_partial: bool = False
) -> ResultDataT
Validate a structured result message.

Source code in pydantic_ai_slim/pydantic_ai/result.py

async def validate_structured_result(
    self, message: _messages.ModelResponse, *, allow_partial: bool = False
) -> ResultDataT:
    """Validate a structured result message."""
    if self._result_schema is not None and self._result_tool_name is not None:
        match = self._result_schema.find_named_tool(message.parts, self._result_tool_name)
        if match is None:
            raise exceptions.UnexpectedModelBehavior(
                f'Invalid response, unable to find tool: {self._result_schema.tool_names()}'
            )

        call, result_tool = match
        result_data = result_tool.validate(call, allow_partial=allow_partial, wrap_validation_errors=False)

        for validator in self._result_validators:
            result_data = await validator.validate(result_data, call, self._run_ctx)
        return result_data
    else:
        text = '\n\n'.join(x.content for x in message.parts if isinstance(x, _messages.TextPart))
        for validator in self._result_validators:
            text = await validator.validate(
                text,
                None,
                self._run_ctx,
            )
        # Since there is no result tool, we can assume that str is compatible with ResultDataT
        return cast(ResultDataT, text)