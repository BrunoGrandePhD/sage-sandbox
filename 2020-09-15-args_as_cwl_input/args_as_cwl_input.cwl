#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

requirements:
  - class: ShellCommandRequirement

baseCommand: wc

inputs:
  args:
    type: string?
    inputBinding:
      position: 1
      shellQuote: false
  file:
    type: File
    inputBinding:
      position: 2

outputs: []
