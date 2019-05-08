def set_default_properties(properties, default_values):
    for val in default_values:
        properties[val] = default_values[val]
    return properties


def set_default_for_customizable_properties(properties, default_values):
    for val in default_values:
        if val not in properties:
            properties[val] = default_values[val]
    return properties
