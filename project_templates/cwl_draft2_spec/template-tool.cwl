#!/usr/bin/env cwl-runner
documentAuthor: ["peter.amstutz@curoverse.com"]
documentDescription: Print the contents of a file to stdout using 'cat' running in a docker container.
class: CommandLineTool
requirements:
  - class: DockerRequirement
    dockerPull: "debian:8"
  - class: ExpressionEngineRequirement
    id: "#js"
    requirements:
      - class: DockerRequirement
        dockerImageId: commonworkflowlanguage/nodejs-engine
    engineCommand: cwlNodeEngine.js
    engineConfig:
      - { include: underscore.js }
      - "var t = function(s) { return _.template(s)({'$job': $job}); };"
  - class: CreateFileRequirement
    fileDef:
      - filename: foo.txt
        fileContent:
          engine: "#js"
          script: 't("The file is <%= $job.file1.path %>\n")'
inputs:
  - id: "#file1"
    type: File
outputs: []
baseCommand: ["cat", "foo.txt"]
