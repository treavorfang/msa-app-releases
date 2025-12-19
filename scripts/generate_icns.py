import os
import subprocess
import shutil

def create_icns(source_png, output_icns):
    if not os.path.exists(source_png):
        print(f"Error: {source_png} not found")
        return False

    iconset_dir = "AppIcon.iconset"
    if os.path.exists(iconset_dir):
        shutil.rmtree(iconset_dir)
    os.makedirs(iconset_dir)

    # Standard sizes for macOS icons
    sizes = [16, 32, 128, 256, 512]
    
    try:
        # Generate different sizes
        for size in sizes:
            # Normal size
            subprocess.run([
                "sips", "-z", str(size), str(size), 
                source_png, 
                "--out", f"{iconset_dir}/icon_{size}x{size}.png"
            ], check=True)
            
            # Retina size (2x)
            subprocess.run([
                "sips", "-z", str(size*2), str(size*2), 
                source_png, 
                "--out", f"{iconset_dir}/icon_{size}x{size}@2x.png"
            ], check=True)

        # Convert iconset to icns
        subprocess.run([
            "iconutil", "-c", "icns", 
            iconset_dir, 
            "-o", output_icns
        ], check=True)
        
        print(f"Successfully created {output_icns}")
        return True

    except Exception as e:
        print(f"Error creating icns: {e}")
        return False
    finally:
        if os.path.exists(iconset_dir):
            shutil.rmtree(iconset_dir)

if __name__ == "__main__":
    create_icns("src/app/static/icons/logo.png", "src/app/static/icons/AppIcon.icns")
