# Building a taxonomy

When dealing with multiple issuers of forms, for example in the case of invoices, issuers or vendors will often use slightly different terminology to refer to the same field a form. For example, *issuer A* may refer to the field "Invoice Date" while *issuer B* may refer to the same field as "Billing date".

Building a Taxonomy to associate these fields with your key field names is vital if any meaningful pre and post-processing is to be achieved alongside extraction using the Unsupervised version of the Forms Recognizer.

The generation of a Taxonomy can be automated using similar techniques as illustrated in this playbook, particularly the search based approach used in [Determining the Form Variation](../../Analysis/Form_Variation/README.md) and the approach used in [AutoLabelling Training](../Training/Auto_Labelling/README.md).

## Logical flow of automating the generation of a Taxonomy

1) Get the Ground Truth Data for the forms
2) OCR the form
3) Search for the GT value for each field to be extracted in the form
4) When found get the text to the left of value's bounding box position on the same line. This is generally the key value on forms but of course it may be above the value as well
5) Capture all unique taxonomy values for a given key
6) Manually inspect and correct

An simple example structure to store these values would be:

```json
{
    "language": "en",
    "InvoiceDate":
        [
            "Invoice Date",
            "Billing Date"
        ],
    "n":
        [
            "",
            ""
        ]
}
```

Back to the [Training section](../README.md)
