#!/bin/bash
version=$1
version=$(jq -r ".version" config.json)
archs=$(cat build.json | jq -rc ".build_from | to_entries")

# Parse architecture options
declare -A archArr
while IFS="=" read -r key value
do
  archArr[$key]="$value"
done < <(jq -r ".build_from|to_entries|map(\"\(.key)=\(.value)\")|.[]" build.json)

# Build and push images
for arch in "${!archArr[@]}"; do
  echo "$arch"
  arch_name=$arch
  arch_img=${archArr[$arch]}
  echo $arch_name
  echo $arch_img
  echo "Building..."
  echo "docker build --build-arg BUILD_FROM=${arch_img} -t "samlehman617/${arch_name}-addon-google-assistant:${version}" ."
  docker build --build-arg BUILD_FROM=${arch_img} -t "samlehman617/${arch_name}-addon-google-assistant:${version}" .
  docker build --build-arg BUILD_FROM=${arch_img} -t "samlehman617/${arch_name}-addon-google-assistant:latest" .
  echo "Pushing..."
  docker push samlehman617/${arch_name}-addon-google-assistant:${version}
  docker push samlehman617/${arch_name}-addon-google-assistant:latest
done
