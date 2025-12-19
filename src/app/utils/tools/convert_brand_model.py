import os

def convert_to_compact_format(input_file, output_file, models_per_line=5):
    """
    Convert a brand_model.ini file from one-model-per-line to compact comma-separated format.
    
    Args:
        input_file (str): Path to the original INI file
        output_file (str): Path to save the converted file
        models_per_line (int): Number of models to put on each line
    """
    brands_config = {}
    current_brand = None
    
    with open(input_file, 'r', encoding='utf-8') as f_in:
        for line in f_in:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                current_brand = line[1:-1]
                brands_config[current_brand] = []
            elif line and current_brand:
                brands_config[current_brand].append(line)
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for brand, models in brands_config.items():
            f_out.write(f"[{brand}]\n")
            
            # Split models into chunks of models_per_line
            for i in range(0, len(models), models_per_line):
                chunk = models[i:i + models_per_line]
                line = ", ".join(chunk)
                
                # Add trailing comma unless it's the last chunk
                if i + models_per_line < len(models):
                    line += ","
                
                f_out.write(f"{line}\n")
            
            # Add an empty line between brands
            f_out.write("\n")

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # The input file is in the same directory as this script
    input_path = os.path.join(script_dir, "brand_model.ini")
    output_path = os.path.join(script_dir, "brand_model_compact.ini")
    
    # Verify input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        print("Please ensure:")
        print("1. This script is placed in the same directory as brand_model.ini")
        print("2. The file is named 'brand_model.ini'")
        print(f"Current script directory: {script_dir}")
        exit(1)
    
    print(f"Converting {input_path} to compact format...")
    convert_to_compact_format(input_path, output_path, models_per_line=5)
    
    print(f"Conversion complete! Output saved to {output_path}")
    print(f"Original file preserved at {input_path}")