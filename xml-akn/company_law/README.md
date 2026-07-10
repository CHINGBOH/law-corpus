# Company Law XML/AKN Workspace

Store immutable structured text files here:

```text
1993.xml
1999.xml
2004.xml
2005.xml
2013.xml
2018.xml
2023.xml
```

Each file should preserve the law's hierarchy:

```text
law → chapter → section → article → paragraph → item
```

The PostgreSQL `legal_versions.xml_uri` column points to these files. The first
database phase only requires article-level extraction into `legal_units`; deeper
paragraph/item extraction can be added later without changing the schema.
