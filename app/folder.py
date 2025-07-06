import os

def create_structure_recursive(base_path, depth=0, output_list=None):
    if output_list is None:
        output_list = []

    # Añadir la estructura de la carpeta base
    indent = "|   " * depth
    try:
        for name in sorted(os.listdir(base_path)):
            path = os.path.join(base_path, name)
            if os.path.isdir(path):  # Si es una carpeta
                output_list.append(f"{indent}|-- {name}/")
                create_structure_recursive(path, depth + 1, output_list)
            elif os.path.isfile(path):  # Si es un archivo
                output_list.append(f"{indent}|-- {name}")
    except PermissionError:
        # Maneja casos donde no se tiene permiso para acceder a ciertas carpetas
        output_list.append(f"{indent}|-- [Permission Denied]")

    return output_list

def generate_project_structure(base_dir=".", output_file="structure.txt"):
    structure_output = [base_dir + "/"]
    structure_output = create_structure_recursive(base_dir, depth=0, output_list=structure_output)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(structure_output))
    
    # También lo imprimimos en la consola para ver el resultado
    print("\n".join(structure_output))
    print(f"Structure of '{base_dir}' saved in '{output_file}'")

# Ejecutar el script
generate_project_structure()