
Microsoft Form Understanding JSON output schema:

```json
{
  "definitions": {},
  "type": "object",
  "title": "The Form Understanding Output Schema",
  "required": [
    "documents"
  ],
  "properties": {
    "documents": {
      "$id": "#/properties/documents",
      "type": "array",
      "title": "The Documents Schema",
      "items": {
        "$id": "#/properties/documents/items",
        "type": "object",
        "title": "The Items Schema",
        "required": [
          "dataRef",
          "pages"
        ],
        "properties": {
          "dataRef": {
            "$id": "#/properties/documents/items/properties/dataRef",
            "type": "string",
            "title": "The Dataref Schema",
            "default": "",
            "examples": [
              "input/dataset/form_1.pdf"
            ],
            "pattern": "^(.*)$"
          },
          "pages": {
            "$id": "#/properties/documents/items/properties/pages",
            "type": "array",
            "title": "The Pages Schema",
            "items": {
              "$id": "#/properties/documents/items/properties/pages/items",
              "type": "object",
              "title": "The Items Schema",
              "required": [
                "number",
                "height",
                "width",
                "clusterId",
                "keyValuePairs",
                "tables"
              ],
              "properties": {
                "number": {
                  "$id": "#/properties/documents/items/properties/pages/items/properties/number",
                  "type": "integer",
                  "title": "The Number Schema",
                  "default": 0,
                  "examples": [
                    1
                  ]
                },
                "height": {
                  "$id": "#/properties/documents/items/properties/pages/items/properties/height",
                  "type": "integer",
                  "title": "The Height Schema",
                  "default": 0,
                  "examples": [
                    842
                  ]
                },
                "width": {
                  "$id": "#/properties/documents/items/properties/pages/items/properties/width",
                  "type": "integer",
                  "title": "The Width Schema",
                  "default": 0,
                  "examples": [
                    595
                  ]
                },
                "clusterId": {
                  "$id": "#/properties/documents/items/properties/pages/items/properties/clusterId",
                  "type": "integer",
                  "title": "The Clusterid Schema",
                  "default": 0,
                  "examples": [
                    0
                  ]
                },
                "keyValuePairs": {
                  "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs",
                  "type": "array",
                  "title": "The Keyvaluepairs Schema",
                  "items": {
                    "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items",
                    "type": "object",
                    "title": "The Items Schema",
                    "required": [
                      "key",
                      "value"
                    ],
                    "properties": {
                      "key": {
                        "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/key",
                        "type": "array",
                        "title": "The Key Schema",
                        "items": {
                          "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/key/items",
                          "type": "object",
                          "title": "The Items Schema",
                          "required": [
                            "text",
                            "boundingBox"
                          ],
                          "properties": {
                            "text": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/key/items/properties/text",
                              "type": "string",
                              "title": "The Text Schema",
                              "default": "",
                              "examples": [
                                "key1"
                              ],
                              "pattern": "^(.*)$"
                            },
                            "boundingBox": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/key/items/properties/boundingBox",
                              "type": "array",
                              "title": "The Boundingbox Schema",
                              "items": {
                                "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/key/items/properties/boundingBox/items",
                                "type": "number",
                                "title": "The Items Schema",
                                "default": 0.0,
                                "examples": [
                                  379.5,
                                  766,
                                  441.2,
                                  766,
                                  441.2,
                                  753.4,
                                  379.5,
                                  753.4
                                ]
                              }
                            }
                          }
                        }
                      },
                      "value": {
                        "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/value",
                        "type": "array",
                        "title": "The Value Schema",
                        "items": {
                          "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/value/items",
                          "type": "object",
                          "title": "The Items Schema",
                          "required": [
                            "text",
                            "boundingBox",
                            "confidence"
                          ],
                          "properties": {
                            "text": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/value/items/properties/text",
                              "type": "string",
                              "title": "The Text Schema",
                              "default": "",
                              "examples": [
                                "value1Line1"
                              ],
                              "pattern": "^(.*)$"
                            },
                            "boundingBox": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/value/items/properties/boundingBox",
                              "type": "array",
                              "title": "The Boundingbox Schema",
                              "items": {
                                "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/value/items/properties/boundingBox/items",
                                "type": "integer",
                                "title": "The Items Schema",
                                "default": 0,
                                "examples": [
                                  443,
                                  765.7,
                                  511.2,
                                  765.7,
                                  511.2,
                                  753.4,
                                  443,
                                  753.4
                                ]
                              }
                            },
                            "confidence": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/keyValuePairs/items/properties/value/items/properties/confidence",
                              "type": "number",
                              "title": "The Confidence Schema",
                              "default": 0.0,
                              "examples": [
                                0.95
                              ]
                            }
                          }
                        }
                      }
                    }
                  }
                },
                "tables": {
                  "$id": "#/properties/documents/items/properties/pages/items/properties/tables",
                  "type": "array",
                  "title": "The Tables Schema",
                  "items": {
                    "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items",
                    "type": "object",
                    "title": "The Items Schema",
                    "required": [
                      "id",
                      "columns"
                    ],
                    "properties": {
                      "id": {
                        "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/id",
                        "type": "string",
                        "title": "The Id Schema",
                        "default": "",
                        "examples": [
                          "table_1"
                        ],
                        "pattern": "^(.*)$"
                      },
                      "columns": {
                        "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns",
                        "type": "array",
                        "title": "The Columns Schema",
                        "items": {
                          "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items",
                          "type": "object",
                          "title": "The Items Schema",
                          "required": [
                            "header",
                            "entries"
                          ],
                          "properties": {
                            "header": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/header",
                              "type": "array",
                              "title": "The Header Schema",
                              "items": {
                                "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/header/items",
                                "type": "object",
                                "title": "The Items Schema",
                                "required": [
                                  "text",
                                  "boundingBox"
                                ],
                                "properties": {
                                  "text": {
                                    "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/header/items/properties/text",
                                    "type": "string",
                                    "title": "The Text Schema",
                                    "default": "",
                                    "examples": [
                                      "col1"
                                    ],
                                    "pattern": "^(.*)$"
                                  },
                                  "boundingBox": {
                                    "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/header/items/properties/boundingBox",
                                    "type": "array",
                                    "title": "The Boundingbox Schema",
                                    "items": {
                                      "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/header/items/properties/boundingBox/items",
                                      "type": "number",
                                      "title": "The Items Schema",
                                      "default": 0.0,
                                      "examples": [
                                        79.7,
                                        633.4,
                                        93.9,
                                        633.4,
                                        93.9,
                                        621.1,
                                        79.7,
                                        621.1
                                      ]
                                    }
                                  }
                                }
                              }
                            },
                            "entries": {
                              "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries",
                              "type": "array",
                              "title": "The Entries Schema",
                              "items": {
                                "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries/items",
                                "type": "array",
                                "title": "The Items Schema",
                                "items": {
                                  "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries/items/items",
                                  "type": "object",
                                  "title": "The Items Schema",
                                  "required": [
                                    "text",
                                    "boundingBox",
                                    "confidence"
                                  ],
                                  "properties": {
                                    "text": {
                                      "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries/items/items/properties/text",
                                      "type": "string",
                                      "title": "The Text Schema",
                                      "default": "",
                                      "examples": [
                                        "col1row1"
                                      ],
                                      "pattern": "^(.*)$"
                                    },
                                    "boundingBox": {
                                      "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries/items/items/properties/boundingBox",
                                      "type": "array",
                                      "title": "The Boundingbox Schema",
                                      "items": {
                                        "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries/items/items/properties/boundingBox/items",
                                        "type": "number",
                                        "title": "The Items Schema",
                                        "default": 0.0,
                                        "examples": [
                                          34.4,
                                          620.6,
                                          64,
                                          620.6,
                                          64,
                                          608.3,
                                          34.4,
                                          608.3
                                        ]
                                      }
                                    },
                                    "confidence": {
                                      "$id": "#/properties/documents/items/properties/pages/items/properties/tables/items/properties/columns/items/properties/entries/items/items/properties/confidence",
                                      "type": "integer",
                                      "title": "The Confidence Schema",
                                      "default": 0,
                                      "examples": [
                                        1
                                      ]
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```
