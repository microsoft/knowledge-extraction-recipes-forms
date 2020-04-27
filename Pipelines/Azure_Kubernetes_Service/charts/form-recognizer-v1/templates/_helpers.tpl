{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "forms.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "forms.fullname" -}}
cognition
{{- end -}}

{{- define "forms.formsrecognizer" -}}
{{ template "forms.fullname" . }}-formsrecognizer
{{- end -}}

{{- define "forms.computervision" -}}
{{ template "forms.fullname" . }}-computervision
{{- end -}}

{{- define "forms.storage" -}}
{{ template "forms.fullname" . }}-storage
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "forms.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "imagePullSecret" }}
{{- printf "{\"auths\": {\"%s\": {\"auth\": \"%s\"}}}" .Values.imageCredentials.registry (printf "%s:%s" .Values.imageCredentials.username .Values.imageCredentials.password | b64enc) | b64enc }}
{{- end }}