import copy
from main import get_client
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
from specklepy.objects.base import Base
#from specklepy.objects.collections import Collection

# TODO: Replace with your project and model IDs
PROJECT_ID_DOWN = "bee3da7616"
MODEL_ID_DOWN = "6b39fd59d4"

PROJECT_ID_UP = "a2d4f63c4b"
MODEL_ID_UP = "d44d739af8"

# TODO: Replace with the applicationId of an object to duplicate
TARGET_APPLICATION_ID = "7c683de4-fa65-4f1f-a047-8549bba36ab9"

# Offset for the duplicated object (move to the right = positive X)
# Note: The model uses millimeters, so 50 meters = 50000 mm
OFFSET_X = 50000.0


def find_object_by_application_id(obj, target_id: str):
    """
    Recursively search for an object with the given applicationId.
    """
    if not isinstance(obj, Base):
        return None
    
    app_id = getattr(obj, "applicationId", None)
    if app_id == target_id:
        return obj
    
    # Search in child elements
    elements = getattr(obj, "@elements", None) or getattr(obj, "elements", [])
    for element in elements or []:
        found = find_object_by_application_id(element, target_id)
        if found:
            return found
    
    return None

def deep_copy_2(obj):
    """
    Create a deep copy of a Speckle object and offset its geometry in X direction.
    """
    # Serialize to dict and deserialize to create a copy
    from specklepy.serialization.base_object_serializer import BaseObjectSerializer
    
    # Create a simple deep copy using Base's serialization
    new_obj = Base()
    
    # Copy all properties
    for key in obj.get_member_names():
        value = getattr(obj, key, None)
        if value is not None:
            try:
                setattr(new_obj, key, copy.deepcopy(value))
            except:
                setattr(new_obj, key, value)
    
    # Clear the id so a new one is generated
    new_obj.id = None
    
    # Generate a new applicationId for the copy
    import uuid
    new_obj.applicationId = str(uuid.uuid4())
    
    return new_obj

def move_obj(obj, offset_x: float):
    """
    Offset geometry in the X direction for various geometry types.
    """
    # Handle displayValue (common in Revit objects)
    display_value = getattr(obj, "displayValue", None) or getattr(obj, "@displayValue", None)
    if display_value:
        if isinstance(display_value, list):
            for mesh in display_value:
                new_vertices = []
                for i in range(0, len(mesh.vertices), 3):
                    new_vertices.append(mesh.vertices[i] + offset_x)  # x + offset
                    new_vertices.append(mesh.vertices[i + 1])          # y
                    new_vertices.append(mesh.vertices[i + 2])          # z
                mesh.vertices = new_vertices
    

def find_object_by_property(obj, property_name: str, target_value: str):
    """
    Recursively search for an object with the given property name and value.
    """
    if not isinstance(obj, Base):
        return None
    
    prop_value = getattr(obj, property_name, None)
    if prop_value == target_value:
        return obj
    
    # Search in child elements
    elements = getattr(obj, "@elements", None) or getattr(obj, "elements", [])
    for element in elements or []:
        found = find_object_by_property(element, property_name, target_value)
        if found:
            return found
    
    return None

def print_members(obj, indent=0):
    """Print all members of an object."""
    prefix = "  " * indent
    
    if isinstance(obj, Base):
        print(f"Type: {prefix}{obj.speckle_type}")
        print(f"Name: {prefix}{obj.name if hasattr(obj, 'name') else 'Unnamed'}")
        
        for name in obj.get_member_names():
            if name.startswith("_"):
                continue
            
            value = getattr(obj, name, None)
            print(f"{prefix}  {name}:")
            print_members(value, indent + 2)
    
    elif isinstance(obj, list):
        print(f"{prefix}[List: {len(obj)} items]")
        if obj:
            print_members(obj[0], indent + 1)  # Show first item
    
    elif isinstance(obj, dict):
        print(f"{prefix}{{Dict: {len(obj)} keys}}")
        for key, value in list(obj.items())[:3]:  # Show first 3
            print(f"{prefix}  {key}:")
            print_members(value, indent + 2)
    
    else:
        # Primitive value
        value_str = str(obj)[:50]  # Limit length
        print(f"{prefix}{value_str}")

def find_all(root, predicate):
    """Find all objects matching a predicate function."""
    results = []
    
    def traverse(obj):
        if isinstance(obj, Base):
            # Check if this object matches
            if predicate(obj):
                results.append(obj)
            
            # Traverse children
            for name in obj.get_member_names():
                if not name.startswith("_"):
                    value = getattr(obj, name, None)
                    traverse(value)
        
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)
        
        elif isinstance(obj, dict):
            for value in obj.values():
                traverse(value)
    
    traverse(root)
    return results

def main():
    # Authenticate
    client = get_client()
    
    # Get the latest version
    versions = client.version.get_versions(MODEL_ID_DOWN, PROJECT_ID_DOWN, limit=1)
    if not versions.items:
        print("No versions found.")
        return
    
    latest_version = versions.items[0]
    print(f"✓ Fetching version: {latest_version.id}")
    
    # Receive the full data tree
    transport = ServerTransport(client=client, stream_id=PROJECT_ID_DOWN)
    data = operations.receive(latest_version.referenced_object, transport)

    #print all data graph
    #print_members(data)

    old = find_all(data, lambda x: x.speckle_type == "Objects.Geometry.BrepX" and x.properties.get("Status") == "Old")
    #print(f"Found {len(old)} olds")

    target_obj = old[0] if old else None
    print(target_obj.id)

    #add new status in parallel
    target_obj.properties["Status_Modified"] = "Old"
    target_obj.properties["Status"] = "New"

    copied_obj = copy.deepcopy(target_obj)
    copied_obj.properties["Status_Modified"] = "Moved2"
    copied_obj.properties["Status"] = "New"
    move_obj(copied_obj, 16000)

    """
    # Find the target object by appid
    print(f"\n--- Duplicate object {TARGET_APPLICATION_ID} ---")
    target_obj = find_object_by_application_id(data, TARGET_APPLICATION_ID)
    print(target_obj)
    
    if not target_obj:
        print(f"✗ Could not find object with applicationId: {TARGET_APPLICATION_ID}")
        return
    
    print(f"✓ Found object: {getattr(target_obj, 'name', 'Unnamed')}")
    print(f"  Type: {getattr(target_obj, 'speckle_type', 'Unknown')}")
    """
    
    #create new modell content
    # Create a fresh Base object for the upstream model (don't receive existing data)
    transport_UP = ServerTransport(client=client, stream_id=PROJECT_ID_UP)
    data_UP = Base()
    #data_UP["@elements"] = [target_obj] #creates array collection
    data_UP["elements"] = [target_obj]
    data_UP["elements"].append(copied_obj)
    data_UP.name = "New_Modules"
    data_UP.properties={"Description":"Model with modified BrepX objects"}
    
    # Send the modified data back
    object_id = operations.send(data_UP, [transport_UP])
    print(f"✓ Sent object: {object_id}")
    
    # Create a new version
    from specklepy.core.api.inputs.version_inputs import CreateVersionInput
    
    version = client.version.create(CreateVersionInput(
        projectId=PROJECT_ID_UP,
        modelId=MODEL_ID_UP ,
        objectId=object_id,
        message=f"Duplicated object with modifications"
    ))
    
    print(f"✓ Created version: {version.id}")
    

if __name__ == "__main__":
    main()
