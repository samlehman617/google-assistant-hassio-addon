#!/bin/bash

# Basic variables
user="samlehman617"
repo_base="addon-google-assistant"

# Grab version from config.json
version=$(jq -r ".version" config.json)

# Create list of version tags
tags=("$version" 'latest')
echo "-----------------------------------------------------"
echo "-----------------------------------------------------"
echo "Tags  : ${tags[@]}"
echo; echo

# Parse architecture options from build.json
declare -A archArr
echo " Arch : Base Image" 
while IFS="=" read -r key value
do
  echo "${key} : ${value}"
  archArr[$key]="$value"
done < <(jq -r ".build_from|to_entries|map(\"\(.key)=\(.value)\")|.[]" build.json)


# Loop through version tags
declare -A multiarch_imgs=()
for ((i=0; i<${#tags[@]}; ++i)); do
  echo "-----------------------------------------------------"
  echo; echo; echo

  # Declare arrays for arch-specific strings
  declare arch_imgs=()
  declare arch_imgs_flags=()

  # Create strings for multiarch images
  tag=${tags[$i]}
  multiarch_imgs["$tag"]="$user/$repo_base:$tag"
  echo "${multiarch_imgs["$tag"]}"

  # Loop through architectures
  for arch in "${!archArr[@]}"; do
    echo "-----------------------------------------------------"

    # Build arch-specific strings
    arch_base=${archArr[$arch]}
    arch_img="$arch-${multiarch_imgs[$tag]}"
    arch_img="$user/$arch-$repo_base:$tag"
    
    # Get arch-specific flags for annotations
    case "$arch" in
      "aarch64") flags="--os linux --arch arm64";;
        "amd64") flags="--os linux --arch amd64";;
        "armhf") flags="--os linux --arch arm --variant v7";;
    esac

    # Add strings to arrays
    arch_imgs_flags+=("$arch_img $flags")
    arch_imgs+=("$arch_img")

    # Print info for image
    echo "Arch: $arch $flags"
    echo "Base: $arch_base"
    echo "Img : $arch_img"
    echo

    # Build and push arch-specific images
    echo "Building $arch_img..."
    echo "docker build --build-arg BUILD_FROM=$arch_base -t $arch_img ."
    docker build --build-arg BUILD_FROM=$arch_base -t $arch_img .
    echo "Pushing $arch_img..."
    docker push $arch_img
  done
  echo; echo; echo
  echo "-----------------------------------------------------"
  
  echo "Creating manifest for ${multiarch_imgs[$tag]}..."
  docker manifest create --amend ${multiarch_imgs[$tag]} ${arch_imgs[@]}
  # Update manifests and push

  echo "FLAGS(${#arch_imgs_flags[@]}): ${arch_imgs_flags[@]}"
  for ((f=0; f<${#arch_imgs_flags[@]}; ++f)); do
    echo "Annotating manifest for ${multiarch_imgs[$tag]}..."
    echo "docker manifest annotate ${multiarch_imgs[$tag]} ${arch_imgs_flags[$f]}"
    docker manifest annotate ${multiarch_imgs[$tag]} ${arch_imgs_flags[$f]}
  done
  # docker manifest annotate ${multiarch_imgs[$tag]} ${arch_imgs_flags[@]}
  echo "Pushing manifest for ${multiarch_imgs[$tag]}..."
  docker manifest push ${multiarch_imgs[$tag]}
  echo "Pushing multiarch image for ${multiarch_imgs[$tag]}..."
  docker push ${multiarch_imgs[$tag]}
done

# We're done here!
exit 0

