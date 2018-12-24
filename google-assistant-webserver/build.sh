#!/bin/bash

# Grab version from config.json
version=$(jq -r ".version" config.json)

# Parse architecture options
declare -A archArr
while IFS="=" read -r key value
do
  archArr[$key]="$value"
done < <(jq -r ".build_from|to_entries|map(\"\(.key)=\(.value)\")|.[]" build.json)

# Build and push images
for arch in "${!archArr[@]}"; do
  arch_name=$arch
  arch_img=${archArr[$arch]}
  echo "Building $arch..."
  echo "docker build --build-arg BUILD_FROM=${arch_img} -t "samlehman617/${arch_name}-addon-google-assistant:${version}" ."
  docker build --build-arg BUILD_FROM=${arch_img} -t "samlehman617/${arch_name}-addon-google-assistant:${version}" .
  docker build --build-arg BUILD_FROM=${arch_img} -t "samlehman617/${arch_name}-addon-google-assistant:latest" .
  echo "Pushing...$arch"
  docker push samlehman617/${arch_name}-addon-google-assistant:${version}
  docker push samlehman617/${arch_name}-addon-google-assistant:latest
done

# Build and push multiarch images
docker push samlehman617/addon-google-assistant:${version}
docker push samlehman617/addon-google-assistant:latest
