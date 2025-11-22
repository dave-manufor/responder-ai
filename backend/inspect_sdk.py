from ibm_watsonx_orchestrate.agent_builder.connections import ExpectedCredentials
import pydantic

print(f"Pydantic version: {pydantic.VERSION}")
try:
    print("Fields:", ExpectedCredentials.model_fields)
except AttributeError:
    try:
        print("Fields:", ExpectedCredentials.__fields__)
    except AttributeError:
        print("Could not access fields directly.")

try:
    # Try instantiating with positional
    t = ExpectedCredentials("test_id")
    print("Positional worked")
except Exception as e:
    print(f"Positional failed: {e}")

try:
    # Try instantiating with 'id'
    t = ExpectedCredentials(id="test_id")
    print("Keyword 'id' worked")
except Exception as e:
    print(f"Keyword 'id' failed: {e}")

try:
    # Try instantiating with 'connection_id'
    t = ExpectedCredentials(connection_id="test_id")
    print("Keyword 'connection_id' worked")
except Exception as e:
    print(f"Keyword 'connection_id' failed: {e}")
