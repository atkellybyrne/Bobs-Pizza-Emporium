#!/usr/bin/env python3
"""
Script to create a pizza icon for the application
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    def create_pizza_icon():
        """Create a simple pizza icon"""
        # Create a 256x256 image (standard icon size)
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw pizza base (circle)
        center = size // 2
        radius = size // 2 - 10
        draw.ellipse([center - radius, center - radius, center + radius, center + radius],
                    fill=(255, 200, 0, 255), outline=(200, 150, 0, 255), width=5)
        
        # Draw pizza crust (outer ring)
        crust_radius = radius - 15
        draw.ellipse([center - crust_radius, center - crust_radius, 
                     center + crust_radius, center + crust_radius],
                    fill=(255, 220, 150, 255), outline=(200, 150, 0, 255), width=3)
        
        # Draw pepperoni slices (circles)
        import math
        num_pepperoni = 6
        for i in range(num_pepperoni):
            angle = (2 * math.pi * i) / num_pepperoni
            x = center + int(crust_radius * 0.6 * math.cos(angle))
            y = center + int(crust_radius * 0.6 * math.sin(angle))
            pepperoni_radius = 20
            draw.ellipse([x - pepperoni_radius, y - pepperoni_radius,
                         x + pepperoni_radius, y + pepperoni_radius],
                        fill=(200, 50, 50, 255), outline=(150, 30, 30, 255), width=2)
        
        # Draw cheese (small yellow circles)
        for i in range(12):
            angle = (2 * math.pi * i) / 12
            x = center + int(crust_radius * 0.8 * math.cos(angle))
            y = center + int(crust_radius * 0.8 * math.sin(angle))
            cheese_radius = 8
            draw.ellipse([x - cheese_radius, y - cheese_radius,
                         x + cheese_radius, y + cheese_radius],
                        fill=(255, 255, 200, 255))
        
        # Save as PNG first
        png_path = 'pizza_icon.png'
        img.save(png_path, 'PNG')
        print(f"✓ Created {png_path}")
        
        # Convert to ICO format (PyInstaller works with ICO on all platforms)
        # Create multiple sizes for ICO
        ico_sizes = [16, 32, 48, 64, 128, 256]
        ico_images = []
        for ico_size in ico_sizes:
            resized = img.resize((ico_size, ico_size), Image.Resampling.LANCZOS)
            ico_images.append(resized)
        
        ico_path = 'pizza_icon.ico'
        ico_images[0].save(ico_path, format='ICO', sizes=[(s, s) for s in ico_sizes])
        print(f"✓ Created {ico_path}")
        
        # For macOS, create ICNS file using iconutil
        try:
            import subprocess
            import tempfile
            import shutil
            
            # Create temporary iconset directory
            iconset_dir = 'pizza_icon.iconset'
            if os.path.exists(iconset_dir):
                shutil.rmtree(iconset_dir)
            os.makedirs(iconset_dir)
            
            # Create all required icon sizes for macOS
            icon_sizes = [
                (16, 'icon_16x16.png'),
                (32, 'icon_16x16@2x.png'),
                (32, 'icon_32x32.png'),
                (64, 'icon_32x32@2x.png'),
                (128, 'icon_128x128.png'),
                (256, 'icon_128x128@2x.png'),
                (256, 'icon_256x256.png'),
                (512, 'icon_256x256@2x.png'),
                (512, 'icon_512x512.png'),
                (1024, 'icon_512x512@2x.png'),
            ]
            
            for size, filename in icon_sizes:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(os.path.join(iconset_dir, filename), 'PNG')
            
            # Convert iconset to icns using iconutil
            icns_path = 'pizza_icon.icns'
            result = subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', icns_path], 
                                  capture_output=True, text=True)
            
            # Clean up iconset directory
            shutil.rmtree(iconset_dir)
            
            if result.returncode == 0 and os.path.exists(icns_path):
                print(f"✓ Created {icns_path} for macOS")
            else:
                print(f"Note: ICNS creation failed, using ICO format")
        except Exception as e:
            print(f"Note: ICNS creation skipped ({e}), using ICO format")
        
        return ico_path
    
    if __name__ == "__main__":
        print("Creating pizza icon...")
        icon_path = create_pizza_icon()
        print(f"\n✓ Icon created successfully: {icon_path}")
        print("You can now use this icon with PyInstaller")

except ImportError:
    print("Pillow (PIL) is not installed. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    print("Please run this script again.")
except Exception as e:
    print(f"Error creating icon: {e}")
    print("\nCreating a simple fallback icon using basic image creation...")
    # Fallback: create a very simple icon
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (256, 256), (255, 200, 0))
        draw = ImageDraw.Draw(img)
        # Simple pizza circle
        draw.ellipse([20, 20, 236, 236], fill=(255, 220, 150), outline=(200, 150, 0), width=5)
        # Simple pepperoni
        draw.ellipse([100, 100, 156, 156], fill=(200, 50, 50))
        img.save('pizza_icon.ico', format='ICO')
        print("✓ Created basic pizza_icon.ico")
    except Exception as e2:
        print(f"Fallback also failed: {e2}")
        print("Please install Pillow: pip install Pillow")

