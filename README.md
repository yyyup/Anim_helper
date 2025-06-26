# Anim Helper

A Blender animation helper addon that provides a collection of tools to streamline the animation workflow.

## Features

### Space Switching Tools
The main panel now groups its sections into collapsible subpanels so you can hide tools you use less often.
- **Knot**: Creates an empty object to control a pose bone or object with constraints
- **Shoulder Lock**: Creates rotation-locked controls for shoulder bones in FK chains
- **Copy Transforms**: Creates empties that copy transforms from bones for advanced animation control

### Animation Baking
- **Easy Bake Animation**: Bake animations with smart frame range detection and various options
- **Duplicate Action for Selected Bones**: Create a new action containing only the animation for selected bones

### Keyframe Management
- **Decimate Keyframes**: Reduce the number of keyframes while preserving motion
- **Mirror Bone Keyframes**: Mirror animation from left to right (or vice versa)
- **Snap Playhead to Strip**: Snap timeline cursor to the beginning of an audio or NLA strip

### Material and Object Management
- **Material Cleanup**: Remove duplicate materials (with dots in their names) and replace with originals
- **Center Objects in XY**: Center objects at the origin while preserving Z position
- **Move to New Collection**: Organize objects by moving them to new collections based on their names

### Facial Animation
- **Rename and Cleanup Actions**: Rename and organize rig and shapekey actions, then push to NLA tracks

### Action Management
- **Delete Actions by Keyword**: Easily remove multiple actions based on a keyword

## Installation

1. Download the latest release (zip file)
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install..." and select the downloaded zip file
4. Enable the "Animation: Anim Helper" addon

## Usage

After installation, the tools appear in the 3D View sidebar. You can choose the name of the tab in the add-on preferences (default is "AH Helper").

### Animation Workflow Tips

1. **Baking Animation**:
   - Use "Smart Bake" to automatically detect keyframe range
   - Enable "Clear Constraints" to remove constraints after baking
   - For selected bones only, make sure to select them before baking

2. **Cleaning Up Keyframes**:
   - Use the Decimate Keys function with an appropriate factor
   - Adjust the factor value to control how many keyframes are kept

3. **Space Switching**:
   - Use Knot for general space switching
   - Use Shoulder Lock specifically for shoulder rotation control
   - Use Copy Transforms for more complex controls with the option to reverse animation

## Requirements

- Blender 4.2.0 or newer

## Credits

- Created by CGstuff
- Refactored and improved for better code organization and reliability

## License

GPL-2.0-or-later