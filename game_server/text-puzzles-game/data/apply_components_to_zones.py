import json
import copy

def merge_components(components_def, zones_def):
    # Create a deep copy to avoid modifying the original
    result = copy.deepcopy(zones_def)
    
    # Function to apply a component to an object
    def apply_component(obj, component_name):
        if component_name not in components_def:
            return
        
        component = components_def[component_name]
        
        # Merge states
        if "states" in component:
            if "initial_state" not in obj:
                obj["initial_state"] = {}
            # Only add state variables that don't already exist in the object
            for state_key, state_value in component["states"].items():
                if state_key not in obj["initial_state"]:
                    obj["initial_state"][state_key] = state_value
        
        # Merge tools
        if "tools" in component:
            if "tools" not in obj:
                obj["tools"] = {}
            for tool in component["tools"]:
                tool_name = tool["name"]
                # Only add tool if it doesn't already exist
                if tool_name not in obj["tools"]:
                    obj["tools"][tool_name] = tool
        
        # Recursively apply implied components
        if "implied_components" in component:
            for implied_component in component["implied_components"]:
                apply_component(obj, implied_component)
    
    # Process all objects in the zones
    for zone in result["zones"].values():
        for subzone in zone["subzones"].values():
            if "objects" in subzone:
                for obj_name, obj_data in subzone["objects"].items():
                    if "components" in obj_data:
                        # Apply each component to the object
                        for component_name in obj_data["components"]:
                            apply_component(obj_data, component_name)
                        # Remove the components list since we've applied them
                        del obj_data["components"]
    
    return result

# Apply components and print result
with open ('components.json', 'r') as f:
    components_def = json.load(f)
with open ('zones_with_components.json', 'r') as f:
    zones_def = json.load(f)
result = merge_components(components_def, zones_def)
with open ('zones.json', 'w') as f:
    json.dump(result, f, indent=2)