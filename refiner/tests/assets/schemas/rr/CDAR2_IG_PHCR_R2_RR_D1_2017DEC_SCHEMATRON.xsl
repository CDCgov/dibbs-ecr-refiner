<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform xmlns:cda="urn:hl7-org:v3"
               xmlns:error="https://doi.org/10.5281/zenodo.1495494#error"
               xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
               xmlns:sch="http://purl.oclc.org/dsdl/schematron"
               xmlns:schxslt="https://doi.org/10.5281/zenodo.1495494"
               xmlns:schxslt-api="https://doi.org/10.5281/zenodo.1495494#api"
               xmlns:sdtc="urn:hl7-org:sdtc"
               xmlns:svs="urn:ihe:iti:svs:2008"
               xmlns:voc="http://www.lantanagroup.com/voc"
               xmlns:xs="http://www.w3.org/2001/XMLSchema"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
               version="2.0">
   <rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:dct="http://purl.org/dc/terms/"
                    xmlns:skos="http://www.w3.org/2004/02/skos/core#">
      <dct:creator>
         <dct:Agent>
            <skos:prefLabel>SchXslt/1.9.5 SAXON/HE 12.5</skos:prefLabel>
            <schxslt.compile.typed-variables xmlns="https://doi.org/10.5281/zenodo.1495494#">true</schxslt.compile.typed-variables>
         </dct:Agent>
      </dct:creator>
      <dct:created>2025-02-20T11:08:40.066704-08:00</dct:created>
   </rdf:Description>
   <xsl:output indent="yes"/>
   <xsl:template match="root()">
      <xsl:variable name="metadata" as="element()?">
         <svrl:metadata xmlns:dct="http://purl.org/dc/terms/"
                        xmlns:skos="http://www.w3.org/2004/02/skos/core#"
                        xmlns:svrl="http://purl.oclc.org/dsdl/svrl">
            <dct:creator>
               <dct:Agent>
                  <skos:prefLabel>
                     <xsl:value-of separator="/"
                                   select="(system-property('xsl:product-name'), system-property('xsl:product-version'))"/>
                  </skos:prefLabel>
               </dct:Agent>
            </dct:creator>
            <dct:created>
               <xsl:value-of select="current-dateTime()"/>
            </dct:created>
            <dct:source>
               <rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/">
                  <dct:creator>
                     <dct:Agent>
                        <skos:prefLabel>SchXslt/1.9.5 SAXON/HE 12.5</skos:prefLabel>
                        <schxslt.compile.typed-variables xmlns="https://doi.org/10.5281/zenodo.1495494#">true</schxslt.compile.typed-variables>
                     </dct:Agent>
                  </dct:creator>
                  <dct:created>2025-02-20T11:08:40.066704-08:00</dct:created>
               </rdf:Description>
            </dct:source>
         </svrl:metadata>
      </xsl:variable>
      <xsl:variable name="report" as="element(schxslt:report)">
         <schxslt:report>
            <xsl:call-template name="d206e161"/>
         </schxslt:report>
      </xsl:variable>
      <xsl:variable name="schxslt:report" as="node()*">
         <xsl:sequence select="$metadata"/>
         <xsl:for-each select="$report/schxslt:document">
            <xsl:for-each select="schxslt:pattern">
               <xsl:sequence select="node()"/>
               <xsl:sequence select="../schxslt:rule[@pattern = current()/@id]/node()"/>
            </xsl:for-each>
         </xsl:for-each>
      </xsl:variable>
      <svrl:schematron-output xmlns:svrl="http://purl.oclc.org/dsdl/svrl">
         <svrl:ns-prefix-in-attribute-values prefix="voc" uri="http://www.lantanagroup.com/voc"/>
         <svrl:ns-prefix-in-attribute-values prefix="svs" uri="urn:ihe:iti:svs:2008"/>
         <svrl:ns-prefix-in-attribute-values prefix="xsi" uri="http://www.w3.org/2001/XMLSchema-instance"/>
         <svrl:ns-prefix-in-attribute-values prefix="sdtc" uri="urn:hl7-org:sdtc"/>
         <svrl:ns-prefix-in-attribute-values prefix="cda" uri="urn:hl7-org:v3"/>
         <xsl:sequence select="$schxslt:report"/>
      </svrl:schematron-output>
   </xsl:template>
   <xsl:template match="text() | @*" mode="#all" priority="-10"/>
   <xsl:template match="/" mode="#all" priority="-10">
      <xsl:apply-templates mode="#current" select="node()"/>
   </xsl:template>
   <xsl:template match="*" mode="#all" priority="-10">
      <xsl:apply-templates mode="#current" select="@*"/>
      <xsl:apply-templates mode="#current" select="node()"/>
   </xsl:template>
   <xsl:template name="d206e161">
      <schxslt:document>
         <schxslt:pattern id="d206e161">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.1-errors"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.1-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e176">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.2-errors"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.2-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e197">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-errors"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e212">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.4-errors"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.4-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e222">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e247">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e268">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e543">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1054">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1079">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1111">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1136">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1170">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1222">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1274">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1318">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1371">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1415">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1449">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1483">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1511">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1551">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1583">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1620">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1657">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1697">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1722">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1756">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1785">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1813">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1834">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1862">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1883">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-errors"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-errors">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1911">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.1-warnings"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.1-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1920">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.2-warnings"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.2-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1938">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-warnings"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1946">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-oid-2.16.840.1.113883.10.20.22.5.4-warnings"
                                    id="p-urn-oid-2.16.840.1.113883.10.20.22.5.4-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1958">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1967">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e1979">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2105">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2257">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2265">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2273">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2281">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2289">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2303">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2316">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2325">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2341">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2356">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2371">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2384">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2393">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2408">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2423">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2432">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2441">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2450">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2458">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2467">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2476">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2485">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2493">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2502">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <schxslt:pattern id="d206e2511">
            <xsl:if test="exists(base-uri(root()))">
               <xsl:attribute name="documents" select="base-uri(root())"/>
            </xsl:if>
            <xsl:for-each select="root()">
               <svrl:active-pattern xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                    name="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-warnings"
                                    id="p-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-warnings">
                  <xsl:attribute name="documents" select="base-uri(.)"/>
               </svrl:active-pattern>
            </xsl:for-each>
         </schxslt:pattern>
         <xsl:apply-templates mode="d206e161" select="root()"/>
      </schxslt:document>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name"
                 priority="72"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e161']">
            <schxslt:rule pattern="d206e161">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.1-errors for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e161">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:given) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7157">
                     <xsl:attribute name="test">count(cda:given) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] given (CONF:81-7157).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:family)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7159">
                     <xsl:attribute name="test">count(cda:family)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] family (CONF:81-7159).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7278-c">
                     <xsl:attribute name="test">not(tested)</xsl:attribute>
                     <svrl:text>*SHALL NOT* have mixed content except for white space (CONF:81-7278).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e161')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr"
                 priority="71"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e176']">
            <schxslt:rule pattern="d206e176">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.2-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.2-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e176">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.2-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:streetAddressLine) &gt;= 1 and count(cda:streetAddressLine) &lt;= 4)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7291-c">
                     <xsl:attribute name="test">count(cda:streetAddressLine) &gt;= 1 and count(cda:streetAddressLine) &lt;= 4</xsl:attribute>
                     <svrl:text>SHALL contain at least one and not more than 4 streetAddressLine (CONF:81-7291).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:city)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7292">
                     <xsl:attribute name="test">count(cda:city)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] city (CONF:81-7292).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7296-c">
                     <xsl:attribute name="test">not(tested)</xsl:attribute>
                     <svrl:text>*SHALL NOT* have mixed content except for white space (CONF:81-7296).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((cda:country='US' and cda:state) or (cda:country!='US') or (not(cda:country) and cda:state) )">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-10024-c">
                     <xsl:attribute name="test">(cda:country='US' and cda:state) or (cda:country!='US') or (not(cda:country) and cda:state) </xsl:attribute>
                     <svrl:text>If the country is US, the state element is required but SHOULD have @nullFlavor if the state is unknown. If country is not specified, it's assumed to be US. If country is something other than US, the state MAY be present but MAY be bound to different vocabularies (CONF:81-10024).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((cda:country='US' and cda:postalCode) or (cda:country!='US') or (not(cda:country) and cda:postalCode))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-10025-c">
                     <xsl:attribute name="test">(cda:country='US' and cda:postalCode) or (cda:country!='US') or (not(cda:country) and cda:postalCode)</xsl:attribute>
                     <svrl:text>If the country is US, the postalCode element is required but SHOULD have @nullFlavor if the postalCode is unknown. If country is not specified, it's assumed to be US. If country is something other than US, the postalCode MAY be present but MAY be bound to different vocabularies (CONF:81-10025).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e176')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name"
                 priority="70"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e197']">
            <schxslt:rule pattern="d206e197">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e197">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(not(tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-9368-c">
                     <xsl:attribute name="test">not(tested)</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] name (CONF:81-9368).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((cda:given and cda:family) or (count(*)=0 and string-length(normalize-space(string(text())))!=0))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-9371-c">
                     <xsl:attribute name="test">(cda:given and cda:family) or (count(*)=0 and string-length(normalize-space(string(text())))!=0)</xsl:attribute>
                     <svrl:text>The content of name *SHALL* be either a conformant Patient Name (PTN.US.FIELDED), or a string (CONF:81-9371).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((cda:given and cda:family) or (count(*)=0))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-9372-c">
                     <xsl:attribute name="test">(cda:given and cda:family) or (count(*)=0)</xsl:attribute>
                     <svrl:text>The string *SHALL NOT* contain name parts (CONF:81-9372).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e197')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime"
                 priority="69"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e212']">
            <schxslt:rule pattern="d206e212">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.4-errors for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.4-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e212">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.4-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(string-length(@value)&gt;=8)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-10127-c">
                     <xsl:attribute name="test">string-length(@value)&gt;=8</xsl:attribute>
                     <svrl:text>*SHALL* be precise to the day (CONF:81-10127).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e212')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]"
                 priority="68"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e222']">
            <schxslt:rule pattern="d206e222">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e222">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7391">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:1098-7391).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='INT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7392">
                     <xsl:attribute name="test">@moodCode='INT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="INT" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:1098-7392).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-16884">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet Patient Education urn:oid:2.16.840.1.113883.11.20.9.34 DYNAMIC (CONF:1098-16884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:statusCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7396">
                     <xsl:attribute name="test">count(cda:statusCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] statusCode (CONF:1098-7396).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:statusCode[@code='completed'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-19106">
                     <xsl:attribute name="test">cda:statusCode[@code='completed']</xsl:attribute>
                     <svrl:text>This statusCode SHALL contain exactly one [1..1] @code="completed" Completed (CodeSystem: HL7ActStatus urn:oid:2.16.840.1.113883.5.14 STATIC) (CONF:1098-19106).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20'][@extension='2014-06-09'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7393">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20'][@extension='2014-06-09'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:1098-7393) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.22.4.20" (CONF:1098-10503). SHALL contain exactly one [1..1] @extension="2014-06-09" (CONF:1098-32598).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e222')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]"
                 priority="67"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e247']">
            <schxslt:rule pattern="d206e247">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-errors for context "cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-errors">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e247">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-errors">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@classCode='DOCCLIN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-31931">
                     <xsl:attribute name="test">@classCode='DOCCLIN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="DOCCLIN" Clinical Document (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:1098-31931).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-31932">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:1098-31932).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-31933">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:1098-31933).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115'][@extension='2014-06-09'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32748">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115'][@extension='2014-06-09'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:1098-32748) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.22.4.115" (CONF:1098-32750). SHALL contain exactly one [1..1] @extension="2014-06-09" (CONF:1098-32749).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32751">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:1098-32751).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e247')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]"
                 priority="66"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e268']">
            <schxslt:rule pattern="d206e268">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-errors for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e268">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:typeId)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5361">
                     <xsl:attribute name="test">count(cda:typeId)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] typeId (CONF:1198-5361).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5363">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:1198-5363).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5253">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:1198-5253).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5266">
                     <xsl:attribute name="test">count(cda:recordTarget) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] recordTarget (CONF:1198-5266).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget[count(cda:patientRole)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5267">
                     <xsl:attribute name="test">cda:recordTarget[count(cda:patientRole)=1]</xsl:attribute>
                     <svrl:text>Such recordTargets SHALL contain exactly one [1..1] patientRole (CONF:1198-5267).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5280">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] telecom (CONF:1198-5280).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:patient)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5283">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:patient)=1]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain exactly one [1..1] patient (CONF:1198-5283).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:birthTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5298">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:birthTime)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] birthTime (CONF:1198-5298).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:guardianPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5385">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:guardianPerson)=1]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHALL contain exactly one [1..1] guardianPerson (CONF:1198-5385).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace[count(cda:place)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5396">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace[count(cda:place)=1]</xsl:attribute>
                     <svrl:text>The birthplace, if present, SHALL contain exactly one [1..1] place (CONF:1198-5396).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place[count(cda:addr)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5397">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place[count(cda:addr)=1]</xsl:attribute>
                     <svrl:text>This place SHALL contain exactly one [1..1] addr (CONF:1198-5397).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5417">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] id (CONF:1198-5417).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5420">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] telecom (CONF:1198-5420).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5444">
                     <xsl:attribute name="test">count(cda:author) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] author (CONF:1198-5444).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author[count(cda:assignedAuthor)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5448">
                     <xsl:attribute name="test">cda:author[count(cda:assignedAuthor)=1]</xsl:attribute>
                     <svrl:text>Such authors SHALL contain exactly one [1..1] assignedAuthor (CONF:1198-5448).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5428">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedAuthor SHALL contain at least one [1..*] telecom (CONF:1198-5428).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer) or cda:dataEnterer[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5442">
                     <xsl:attribute name="test">not(cda:dataEnterer) or cda:dataEnterer[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>The dataEnterer, if present, SHALL contain exactly one [1..1] assignedEntity (CONF:1198-5442).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5443">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:1198-5443).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5466">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] telecom (CONF:1198-5466).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:assignedPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5469">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:assignedPerson)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain exactly one [1..1] assignedPerson (CONF:1198-5469).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:custodian)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5519">
                     <xsl:attribute name="test">count(cda:custodian)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] custodian (CONF:1198-5519).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian[count(cda:assignedCustodian)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5520">
                     <xsl:attribute name="test">cda:custodian[count(cda:assignedCustodian)=1]</xsl:attribute>
                     <svrl:text>This custodian SHALL contain exactly one [1..1] assignedCustodian (CONF:1198-5520).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian[count(cda:representedCustodianOrganization)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5521">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian[count(cda:representedCustodianOrganization)=1]</xsl:attribute>
                     <svrl:text>This assignedCustodian SHALL contain exactly one [1..1] representedCustodianOrganization (CONF:1198-5521).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5522">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain at least one [1..*] id (CONF:1198-5522).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:telecom)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5525">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:telecom)=1]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain exactly one [1..1] telecom (CONF:1198-5525).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:informationRecipient) or cda:informationRecipient[count(cda:intendedRecipient)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5566">
                     <xsl:attribute name="test">not(cda:informationRecipient) or cda:informationRecipient[count(cda:intendedRecipient)=1]</xsl:attribute>
                     <svrl:text>The informationRecipient, if present, SHALL contain exactly one [1..1] intendedRecipient (CONF:1198-5566).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:signatureCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5583">
                     <xsl:attribute name="test">not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:signatureCode)=1]</xsl:attribute>
                     <svrl:text>The legalAuthenticator, if present, SHALL contain exactly one [1..1] signatureCode (CONF:1198-5583).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5585">
                     <xsl:attribute name="test">not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>The legalAuthenticator, if present, SHALL contain exactly one [1..1] assignedEntity (CONF:1198-5585).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5586">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:1198-5586).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5595">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] telecom (CONF:1198-5595).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:assignedPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5597">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:assignedPerson)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain exactly one [1..1] assignedPerson (CONF:1198-5597).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:inFulfillmentOf) or cda:inFulfillmentOf[count(cda:order)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9953">
                     <xsl:attribute name="test">not(cda:inFulfillmentOf) or cda:inFulfillmentOf[count(cda:order)=1]</xsl:attribute>
                     <svrl:text>The inFulfillmentOf, if present, SHALL contain exactly one [1..1] order (CONF:1198-9953).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf) or cda:documentationOf[count(cda:serviceEvent)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14836">
                     <xsl:attribute name="test">not(cda:documentationOf) or cda:documentationOf[count(cda:serviceEvent)=1]</xsl:attribute>
                     <svrl:text>The documentationOf, if present, SHALL contain exactly one [1..1] serviceEvent (CONF:1198-14836).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:effectiveTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14837">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:effectiveTime)=1]</xsl:attribute>
                     <svrl:text>This serviceEvent SHALL contain exactly one [1..1] effectiveTime (CONF:1198-14837).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14841">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>The performer, if present, SHALL contain exactly one [1..1] assignedEntity (CONF:1198-14841).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14846">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:1198-14846).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:componentOf) or cda:componentOf[count(cda:encompassingEncounter)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9956">
                     <xsl:attribute name="test">not(cda:componentOf) or cda:componentOf[count(cda:encompassingEncounter)=1]</xsl:attribute>
                     <svrl:text>The componentOf, if present, SHALL contain exactly one [1..1] encompassingEncounter (CONF:1198-9956).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5256-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:1198-5256).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:realmCode[@code='US'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16791">
                     <xsl:attribute name="test">count(cda:realmCode[@code='US'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] realmCode="US" (CONF:1198-16791).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:typeId[@root='2.16.840.1.113883.1.3'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5250">
                     <xsl:attribute name="test">cda:typeId[@root='2.16.840.1.113883.1.3']</xsl:attribute>
                     <svrl:text>This typeId SHALL contain exactly one [1..1] @root="2.16.840.1.113883.1.3" (CONF:1198-5250).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:typeId[@extension='POCD_HD000040'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5251">
                     <xsl:attribute name="test">cda:typeId[@extension='POCD_HD000040']</xsl:attribute>
                     <svrl:text>This typeId SHALL contain exactly one [1..1] @extension="POCD_HD000040" (CONF:1198-5251).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9992-c">
                     <xsl:attribute name="test">.</xsl:attribute>
                     <svrl:text>This code *SHALL* specify the particular kind of document (e.g., History and Physical, Discharge Summary, Progress Note) (CONF:1198-9992).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:title)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5254">
                     <xsl:attribute name="test">count(cda:title)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] title (CONF:1198-5254).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:confidentialityCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5259">
                     <xsl:attribute name="test">count(cda:confidentialityCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] confidentialityCode, which SHOULD be selected from ValueSet HL7 BasicConfidentialityKind urn:oid:2.16.840.1.113883.1.11.16926 STATIC (CONF:1198-5259).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:languageCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5372">
                     <xsl:attribute name="test">count(cda:languageCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] languageCode, which SHALL be selected from ValueSet Language urn:oid:2.16.840.1.113883.1.11.11526 DYNAMIC (CONF:1198-5372).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-6380-c">
                     <xsl:attribute name="test">count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0</xsl:attribute>
                     <svrl:text>If  setId is present versionNumber *SHALL* be present (CONF:1198-6380).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-6387-c">
                     <xsl:attribute name="test">count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0</xsl:attribute>
                     <svrl:text>If versionNumber is present setId *SHALL* be present (CONF:1198-6387).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5268">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] id (CONF:1198-5268).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5271-c">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5271).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget/cda:patientRole/cda:patient) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:name))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5284-c">
                     <xsl:attribute name="test">count(cda:recordTarget/cda:patientRole/cda:patient) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:name)</xsl:attribute>
                     <svrl:text>This patient SHALL contain at least one [1..*] US Realm Patient Name (PTN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1) (CONF:1198-5284).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:administrativeGenderCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-6394">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:administrativeGenderCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] administrativeGenderCode, which SHALL be selected from ValueSet Administrative Gender (HL7 V3) urn:oid:2.16.840.1.113883.1.11.1 DYNAMIC (CONF:1198-6394).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 4)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5299-c">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 4</xsl:attribute>
                     <svrl:text>*SHALL* be precise to year (CONF:1198-5299).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:raceCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5322">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:raceCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] raceCode, which SHALL be selected from ValueSet Race Category Excluding Nulls urn:oid:2.16.840.1.113883.3.2074.1.1.3 DYNAMIC (CONF:1198-5322).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:ethnicGroupCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5323">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:ethnicGroupCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] ethnicGroupCode, which SHALL be selected from ValueSet Ethnicity urn:oid:2.16.840.1.114222.4.11.837 DYNAMIC (CONF:1198-5323).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5386-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>This guardianPerson SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5386).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:languageCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5407">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:languageCode)=1]</xsl:attribute>
                     <svrl:text>The languageCommunication, if present, SHALL contain exactly one [1..1] languageCode, which SHALL be selected from ValueSet Language urn:oid:2.16.840.1.113883.1.11.11526 DYNAMIC (CONF:1198-5407).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/sdtc:raceCode) or cda:recordTarget/cda:patientRole/cda:patient/cda:raceCode)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-31347-c">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/sdtc:raceCode) or cda:recordTarget/cda:patientRole/cda:patient/cda:raceCode</xsl:attribute>
                     <svrl:text>If sdtc:raceCode is present, then the patient *SHALL* contain [[]1..1[]] raceCode (CONF:1198-31347).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:name) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5419">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:name) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] name (CONF:1198-5419).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5422-c">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5422).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5445-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>Such authors SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:1198-5445).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5449">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedAuthor SHALL contain at least one [1..*] id (CONF:1198-5449).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16788">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code]</xsl:attribute>
                     <svrl:text>The code, if present, SHALL contain exactly one [1..1] @code, which SHOULD be selected from ValueSet Healthcare Provider Taxonomy (HIPAA) urn:oid:2.16.840.1.114222.4.11.1066 DYNAMIC (CONF:1198-16788).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author/cda:assignedAuthor) &lt;= count(cda:author/cda:assignedAuthor/cda:addr))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5452-c">
                     <xsl:attribute name="test">count(cda:author/cda:assignedAuthor) &lt;= count(cda:author/cda:assignedAuthor/cda:addr)</xsl:attribute>
                     <svrl:text>This assignedAuthor SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5452).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16789-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>The assignedPerson, if present, SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-16789).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:manufacturerModelName)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16784">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:manufacturerModelName)=1]</xsl:attribute>
                     <svrl:text>The assignedAuthoringDevice, if present, SHALL contain exactly one [1..1] manufacturerModelName (CONF:1198-16784).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:softwareName)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16785">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:softwareName)=1]</xsl:attribute>
                     <svrl:text>The assignedAuthoringDevice, if present, SHALL contain exactly one [1..1] softwareName (CONF:1198-16785).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)=1] and not(cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)!=1] ))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16790-c">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)=1] and not(cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)!=1] )</xsl:attribute>
                     <svrl:text>There *SHALL* be exactly one assignedAuthor/assignedPerson or exactly one assignedAuthor/assignedAuthoringDevice (CONF:1198-16790).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:dataEnterer/cda:assignedEntity) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:addr))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5460-c">
                     <xsl:attribute name="test">count(cda:dataEnterer/cda:assignedEntity) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:addr)</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5460).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5470-c">
                     <xsl:attribute name="test">count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name)</xsl:attribute>
                     <svrl:text>This assignedPerson SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5470).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5524">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain exactly one [1..1] name (CONF:1198-5524).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:addr)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5559-c">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:addr)=1]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5559).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient) &lt;= count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5568-c">
                     <xsl:attribute name="test">count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient) &lt;= count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name)</xsl:attribute>
                     <svrl:text>The informationRecipient, if present, SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5568).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization) or cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5578">
                     <xsl:attribute name="test">not(cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization) or cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHALL contain exactly one [1..1] name (CONF:1198-5578).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5580-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>The legalAuthenticator, if present, SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:1198-5580).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:signatureCode) or cda:legalAuthenticator/cda:signatureCode[@code='S'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5584">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:signatureCode) or cda:legalAuthenticator/cda:signatureCode[@code='S']</xsl:attribute>
                     <svrl:text>This signatureCode SHALL contain exactly one [1..1] @code="S" (CodeSystem: HL7ParticipationSignature urn:oid:2.16.840.1.113883.5.89 STATIC) (CONF:1198-5584).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator) or cda:legalAuthenticator/cda:assignedEntity[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5589-c">
                     <xsl:attribute name="test">not(cda:legalAuthenticator) or cda:legalAuthenticator/cda:assignedEntity[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5589).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5598-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>This assignedPerson SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5598).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant) = count( cda:participant/cda:associatedEntity[cda:associatedPerson | cda:scopingOrganization]))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-10006-c">
                     <xsl:attribute name="test">count(cda:participant) = count( cda:participant/cda:associatedEntity[cda:associatedPerson | cda:scopingOrganization])</xsl:attribute>
                     <svrl:text>*SHALL* contain associatedEntity/associatedPerson *AND/OR* associatedEntity/scopingOrganization (CONF:1198-10006).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:inFulfillmentOf/cda:order) or cda:inFulfillmentOf/cda:order[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9954">
                     <xsl:attribute name="test">not(cda:inFulfillmentOf/cda:order) or cda:inFulfillmentOf/cda:order[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This order SHALL contain at least one [1..*] id (CONF:1198-9954).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:effectiveTime) or cda:documentationOf/cda:serviceEvent/cda:effectiveTime[count(cda:low)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14838">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:effectiveTime) or cda:documentationOf/cda:serviceEvent/cda:effectiveTime[count(cda:low)=1]</xsl:attribute>
                     <svrl:text>This effectiveTime SHALL contain exactly one [1..1] low (CONF:1198-14838).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[@typeCode and @typeCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.19601']/voc:code/@value])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14840">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[@typeCode and @typeCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.19601']/voc:code/@value]</xsl:attribute>
                     <svrl:text>The performer, if present, SHALL contain exactly one [1..1] @typeCode, which SHALL be selected from ValueSet x_ServiceEventPerformer urn:oid:2.16.840.1.113883.1.11.19601 STATIC (CONF:1198-14840).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9959">
                     <xsl:attribute name="test">not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain at least one [1..*] id (CONF:1198-9959).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:effectiveTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9958">
                     <xsl:attribute name="test">not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:effectiveTime)=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] effectiveTime (CONF:1198-9958).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32948-c">
                     <xsl:attribute name="test">.</xsl:attribute>
                     <svrl:text>This code *SHALL* be drawn from the LOINC document type ontology (LOINC codes where SCALE = DOC) (CONF:1198-32948).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1'][@extension='2015-08-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5252">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1'][@extension='2015-08-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:1198-5252) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.22.1.1" (CONF:1198-10036). SHALL contain exactly one [1..1] @extension="2015-08-01" (CONF:1198-32503).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e268')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]"
                 priority="65"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e543']">
            <schxslt:rule pattern="d206e543">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-errors for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e543">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:componentOf)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-1">
                     <xsl:attribute name="test">count(cda:componentOf)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] componentOf (CONF:3315-1).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf[count(cda:encompassingEncounter)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-2">
                     <xsl:attribute name="test">cda:componentOf[count(cda:encompassingEncounter)=1]</xsl:attribute>
                     <svrl:text>This componentOf SHALL contain exactly one [1..1] encompassingEncounter (CONF:3315-2).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter[count(cda:effectiveTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-3">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter[count(cda:effectiveTime)=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] effectiveTime (CONF:3315-3).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter[count(cda:responsibleParty)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-4">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter[count(cda:responsibleParty)=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] responsibleParty (CONF:3315-4).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-5">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>This responsibleParty SHALL contain exactly one [1..1] assignedEntity (CONF:3315-5).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:assignedPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-6">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:assignedPerson)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain exactly one [1..1] assignedPerson (CONF:3315-6).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-7">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:3315-7).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:representedOrganization)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-8">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:representedOrganization)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain exactly one [1..1] representedOrganization (CONF:3315-8).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter[count(cda:location)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-9">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter[count(cda:location)=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] location (CONF:3315-9).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location[count(cda:healthCareFacility)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-10">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location[count(cda:healthCareFacility)=1]</xsl:attribute>
                     <svrl:text>This location SHALL contain exactly one [1..1] healthCareFacility (CONF:3315-10).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:id)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-11">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:id)=1]</xsl:attribute>
                     <svrl:text>This healthCareFacility SHALL contain exactly one [1..1] id (CONF:3315-11).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:location)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-12">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:location)=1]</xsl:attribute>
                     <svrl:text>This healthCareFacility SHALL contain exactly one [1..1] location (CONF:3315-12).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:serviceProviderOrganization)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-13">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:serviceProviderOrganization)=1]</xsl:attribute>
                     <svrl:text>This healthCareFacility SHALL contain exactly one [1..1] serviceProviderOrganization (CONF:3315-13).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:component)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-14">
                     <xsl:attribute name="test">count(cda:component)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] component (CONF:3315-14).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-28">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-28) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.1.2" (CONF:3315-66). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-67).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-29">
                     <xsl:attribute name="test">count(cda:recordTarget)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] recordTarget (CONF:3315-29).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget[count(cda:patientRole)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-30">
                     <xsl:attribute name="test">cda:recordTarget[count(cda:patientRole)=1]</xsl:attribute>
                     <svrl:text>This recordTarget SHALL contain exactly one [1..1] patientRole (CONF:3315-30).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:patient)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-31">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:patient)=1]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain exactly one [1..1] patient (CONF:3315-31).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-34">
                     <xsl:attribute name="test">count(cda:author) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] author (CONF:3315-34).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-35-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>Such authors SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:3315-35).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:effectiveTime)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-36">
                     <xsl:attribute name="test">count(cda:effectiveTime)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] effectiveTime (CONF:3315-36).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-37-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>This assignedPerson SHALL contain exactly one [1..1] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:3315-37).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:effectiveTime[not(@nullFlavor)])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-38">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:effectiveTime[not(@nullFlavor)]</xsl:attribute>
                     <svrl:text>This effectiveTime SHALL NOT contain [0..0] @nullFlavor (CONF:3315-38).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:effectiveTime[count(cda:low)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-39">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:effectiveTime[count(cda:low)=1]</xsl:attribute>
                     <svrl:text>This effectiveTime SHALL contain exactly one [1..1] low (CONF:3315-39).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:effectiveTime[count(cda:high)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-40">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:effectiveTime[count(cda:high)=1]</xsl:attribute>
                     <svrl:text>This effectiveTime SHALL contain exactly one [1..1] high (CONF:3315-40).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:id[@root])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-41">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:id[@root]</xsl:attribute>
                     <svrl:text>Such ids SHALL contain exactly one [1..1] @root (CONF:3315-41).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-43">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This representedOrganization SHALL contain exactly one [1..1] name (CONF:3315-43).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-44-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>This representedOrganization SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-44).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-45-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-45).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-46">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] telecom (CONF:3315-46).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:id[@root])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-47">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:id[@root]</xsl:attribute>
                     <svrl:text>This id SHALL contain exactly one [1..1] @root (CONF:3315-47).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-49-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>This location SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-49).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-50">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This serviceProviderOrganization SHALL contain exactly one [1..1] name (CONF:3315-50).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-51">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This serviceProviderOrganization SHALL contain at least one [1..*] telecom (CONF:3315-51).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-52-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>This serviceProviderOrganization SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-52).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-53">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This healthCareFacility SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet ServiceDeliveryLocationRoleType urn:oid:2.16.840.1.113883.1.11.17660 (CONF:3315-53).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-54">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain at least one [1..*] id (CONF:3315-54).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-55">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet ActEncounterCode urn:oid:2.16.840.1.113883.1.11.13955 (CONF:3315-55).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-68-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>The guardian, if present, SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-68).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-69">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHALL contain at least one [1..*] telecom (CONF:3315-69).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:guardianPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-70">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:guardianPerson)=1]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHALL contain exactly one [1..1] guardianPerson (CONF:3315-70).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(( not( cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedInd[ @value='true']) and not( cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedTime)) or ( cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedInd[ @value='true'] and cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedTime))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-71-c">
                     <xsl:attribute name="test">( not( cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedInd[ @value='true']) and not( cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedTime)) or ( cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedInd[ @value='true'] and cda:recordTarget/cda:patientRole/cda:patient/sdtc:deceasedTime)</xsl:attribute>
                     <svrl:text>If sdtc:deceasedInd is true then sdtc:deceasedTime *SHALL* be present (CONF:3315-71).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:languageCommunication) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-72">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:languageCommunication) &gt; 0]</xsl:attribute>
                     <svrl:text>This patient SHALL contain at least one [1..*] languageCommunication (CONF:3315-72).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(sdtc:deceasedInd)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-73">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(sdtc:deceasedInd)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] sdtc:deceasedInd (CONF:3315-73).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-74">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] id (CONF:3315-74).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-75-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-75).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:time[not(@nullFlavor)])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-76">
                     <xsl:attribute name="test">cda:author/cda:time[not(@nullFlavor)]</xsl:attribute>
                     <svrl:text>This time SHALL NOT contain [0..0] @nullFlavor (CONF:3315-76).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author[count(cda:assignedAuthor)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-77">
                     <xsl:attribute name="test">cda:author[count(cda:assignedAuthor)=1]</xsl:attribute>
                     <svrl:text>Such authors SHALL contain exactly one [1..1] assignedAuthor (CONF:3315-77).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:effectiveTime[not(@nullFlavor)])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-78">
                     <xsl:attribute name="test">cda:effectiveTime[not(@nullFlavor)]</xsl:attribute>
                     <svrl:text>This effectiveTime SHALL NOT contain [0..0] @nullFlavor (CONF:3315-78).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-79">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-79).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:title)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-80">
                     <xsl:attribute name="test">count(cda:title)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] title (CONF:3315-80).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:informationRecipient[@typeCode='PRCP'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-83">
                     <xsl:attribute name="test">count(cda:informationRecipient[@typeCode='PRCP'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] informationRecipient (CONF:3315-83) such that it SHALL contain exactly one [1..1] @typeCode="PRCP" Primary information recipient (CodeSystem: HL7ParticipationType urn:oid:2.16.840.1.113883.5.90) (CONF:3315-701).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:component[count(cda:structuredBody)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-141">
                     <xsl:attribute name="test">cda:component[count(cda:structuredBody)=1]</xsl:attribute>
                     <svrl:text>This component SHALL contain exactly one [1..1] structuredBody (CONF:3315-141).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='88085-6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-359">
                     <xsl:attribute name="test">cda:code[@code='88085-6']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="88085-6" Reportability response report Document Public health (CONF:3315-359).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-360">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.1']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.1" (CodeSystem: LOINC urn:oid:2.16.840.1.113883.6.1) (CONF:3315-360).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:component/cda:structuredBody[count(cda:component[count(cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']])=1])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-629">
                     <xsl:attribute name="test">cda:component/cda:structuredBody[count(cda:component[count(cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']])=1])=1]</xsl:attribute>
                     <svrl:text>This structuredBody SHALL contain exactly one [1..1] component (CONF:3315-629) such that it SHALL contain exactly one [1..1] Electronic Initial Case Report Section (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.2.3:2017-04-01) (CONF:3315-630).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((count( //cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=1 and count( //cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1']] )=0) or ( count(//cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=0 and count(//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1']])=1))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-635-c">
                     <xsl:attribute name="test">(count( //cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=1 and count( //cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1']] )=0) or ( count(//cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=0 and count(//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1']])=1)</xsl:attribute>
                     <svrl:text>The Reportability Response Subject Section *SHALL* be present if the eICR CDA document was processed or was processed with a warning or severe warning (eICR Processing Status/code="RRVS19" or "RRVS20" or "RRVS21") and *SHALL NOT* be present if the eICR CDA document was not processed (eICR ProcessingStatus/code="RRVS22") (CONF:3315-635).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((count( //cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=1 and count( //cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2']] )=0) or ( count(//cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=0 and count(//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2']])=1))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-636-c">
                     <xsl:attribute name="test">(count( //cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=1 and count( //cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2']] )=0) or ( count(//cda:act[ cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29']]/cda:code[@code='RRVS22'])=0 and count(//cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2']])=1)</xsl:attribute>
                     <svrl:text>The Reportability Response Summary Section *SHALL* be present if the eICR CDA document was processed or was processed with a warning or severe warning (eICR Processing Status/code="RRVS19" or "RRVS20" or "RRVS21") and *SHALL NOT* be present if the eICR CDA document was not processed (eICR ProcessingStatus/code="RRVS22") (CONF:3315-636).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:name) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-739">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:name) &gt; 0]</xsl:attribute>
                     <svrl:text>This patient SHALL contain at least one [1..*] name (CONF:3315-739).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:birthTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-742">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:birthTime)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] birthTime (CONF:3315-742).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:raceCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-745">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:raceCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] raceCode (CONF:3315-745).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:ethnicGroupCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-747">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:ethnicGroupCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] ethnicGroupCode (CONF:3315-747).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-753">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] telecom (CONF:3315-753).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:administrativeGenderCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-754">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:administrativeGenderCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] administrativeGenderCode (CONF:3315-754).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson[count(cda:name) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-755">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson[count(cda:name) &gt; 0]</xsl:attribute>
                     <svrl:text>This guardianPerson SHALL contain at least one [1..*] name (CONF:3315-755).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:typeId)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5361">
                     <xsl:attribute name="test">count(cda:typeId)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] typeId (CONF:1198-5361).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5363">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:1198-5363).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5253">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:1198-5253).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5266">
                     <xsl:attribute name="test">count(cda:recordTarget) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] recordTarget (CONF:1198-5266).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget[count(cda:patientRole)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5267">
                     <xsl:attribute name="test">cda:recordTarget[count(cda:patientRole)=1]</xsl:attribute>
                     <svrl:text>Such recordTargets SHALL contain exactly one [1..1] patientRole (CONF:1198-5267).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5280">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] telecom (CONF:1198-5280).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:patient)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5283">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:patient)=1]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain exactly one [1..1] patient (CONF:1198-5283).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:birthTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5298">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:birthTime)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] birthTime (CONF:1198-5298).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:guardianPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5385">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:guardianPerson)=1]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHALL contain exactly one [1..1] guardianPerson (CONF:1198-5385).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace[count(cda:place)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5396">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace[count(cda:place)=1]</xsl:attribute>
                     <svrl:text>The birthplace, if present, SHALL contain exactly one [1..1] place (CONF:1198-5396).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place[count(cda:addr)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5397">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place[count(cda:addr)=1]</xsl:attribute>
                     <svrl:text>This place SHALL contain exactly one [1..1] addr (CONF:1198-5397).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5417">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] id (CONF:1198-5417).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5420">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] telecom (CONF:1198-5420).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5444">
                     <xsl:attribute name="test">count(cda:author) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] author (CONF:1198-5444).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author[count(cda:assignedAuthor)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5448">
                     <xsl:attribute name="test">cda:author[count(cda:assignedAuthor)=1]</xsl:attribute>
                     <svrl:text>Such authors SHALL contain exactly one [1..1] assignedAuthor (CONF:1198-5448).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5428">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedAuthor SHALL contain at least one [1..*] telecom (CONF:1198-5428).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer) or cda:dataEnterer[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5442">
                     <xsl:attribute name="test">not(cda:dataEnterer) or cda:dataEnterer[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>The dataEnterer, if present, SHALL contain exactly one [1..1] assignedEntity (CONF:1198-5442).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5443">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:1198-5443).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5466">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] telecom (CONF:1198-5466).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:assignedPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5469">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity) or cda:dataEnterer/cda:assignedEntity[count(cda:assignedPerson)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain exactly one [1..1] assignedPerson (CONF:1198-5469).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:custodian)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5519">
                     <xsl:attribute name="test">count(cda:custodian)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] custodian (CONF:1198-5519).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian[count(cda:assignedCustodian)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5520">
                     <xsl:attribute name="test">cda:custodian[count(cda:assignedCustodian)=1]</xsl:attribute>
                     <svrl:text>This custodian SHALL contain exactly one [1..1] assignedCustodian (CONF:1198-5520).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian[count(cda:representedCustodianOrganization)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5521">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian[count(cda:representedCustodianOrganization)=1]</xsl:attribute>
                     <svrl:text>This assignedCustodian SHALL contain exactly one [1..1] representedCustodianOrganization (CONF:1198-5521).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5522">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain at least one [1..*] id (CONF:1198-5522).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:telecom)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5525">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:telecom)=1]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain exactly one [1..1] telecom (CONF:1198-5525).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:informationRecipient) or cda:informationRecipient[count(cda:intendedRecipient)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5566">
                     <xsl:attribute name="test">not(cda:informationRecipient) or cda:informationRecipient[count(cda:intendedRecipient)=1]</xsl:attribute>
                     <svrl:text>The informationRecipient, if present, SHALL contain exactly one [1..1] intendedRecipient (CONF:1198-5566).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:signatureCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5583">
                     <xsl:attribute name="test">not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:signatureCode)=1]</xsl:attribute>
                     <svrl:text>The legalAuthenticator, if present, SHALL contain exactly one [1..1] signatureCode (CONF:1198-5583).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5585">
                     <xsl:attribute name="test">not(cda:legalAuthenticator) or cda:legalAuthenticator[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>The legalAuthenticator, if present, SHALL contain exactly one [1..1] assignedEntity (CONF:1198-5585).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5586">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:1198-5586).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5595">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] telecom (CONF:1198-5595).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:assignedPerson)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5597">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity) or cda:legalAuthenticator/cda:assignedEntity[count(cda:assignedPerson)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain exactly one [1..1] assignedPerson (CONF:1198-5597).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:inFulfillmentOf) or cda:inFulfillmentOf[count(cda:order)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9953">
                     <xsl:attribute name="test">not(cda:inFulfillmentOf) or cda:inFulfillmentOf[count(cda:order)=1]</xsl:attribute>
                     <svrl:text>The inFulfillmentOf, if present, SHALL contain exactly one [1..1] order (CONF:1198-9953).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf) or cda:documentationOf[count(cda:serviceEvent)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14836">
                     <xsl:attribute name="test">not(cda:documentationOf) or cda:documentationOf[count(cda:serviceEvent)=1]</xsl:attribute>
                     <svrl:text>The documentationOf, if present, SHALL contain exactly one [1..1] serviceEvent (CONF:1198-14836).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:effectiveTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14837">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:effectiveTime)=1]</xsl:attribute>
                     <svrl:text>This serviceEvent SHALL contain exactly one [1..1] effectiveTime (CONF:1198-14837).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[count(cda:assignedEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14841">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[count(cda:assignedEntity)=1]</xsl:attribute>
                     <svrl:text>The performer, if present, SHALL contain exactly one [1..1] assignedEntity (CONF:1198-14841).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14846">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] id (CONF:1198-14846).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:componentOf) or cda:componentOf[count(cda:encompassingEncounter)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9956">
                     <xsl:attribute name="test">not(cda:componentOf) or cda:componentOf[count(cda:encompassingEncounter)=1]</xsl:attribute>
                     <svrl:text>The componentOf, if present, SHALL contain exactly one [1..1] encompassingEncounter (CONF:1198-9956).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5256-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:1198-5256).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:realmCode[@code='US'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16791">
                     <xsl:attribute name="test">count(cda:realmCode[@code='US'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] realmCode="US" (CONF:1198-16791).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:typeId[@root='2.16.840.1.113883.1.3'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5250">
                     <xsl:attribute name="test">cda:typeId[@root='2.16.840.1.113883.1.3']</xsl:attribute>
                     <svrl:text>This typeId SHALL contain exactly one [1..1] @root="2.16.840.1.113883.1.3" (CONF:1198-5250).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:typeId[@extension='POCD_HD000040'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5251">
                     <xsl:attribute name="test">cda:typeId[@extension='POCD_HD000040']</xsl:attribute>
                     <svrl:text>This typeId SHALL contain exactly one [1..1] @extension="POCD_HD000040" (CONF:1198-5251).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9992-c">
                     <xsl:attribute name="test">.</xsl:attribute>
                     <svrl:text>This code *SHALL* specify the particular kind of document (e.g., History and Physical, Discharge Summary, Progress Note) (CONF:1198-9992).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:title)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5254">
                     <xsl:attribute name="test">count(cda:title)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] title (CONF:1198-5254).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:confidentialityCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5259">
                     <xsl:attribute name="test">count(cda:confidentialityCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] confidentialityCode, which SHOULD be selected from ValueSet HL7 BasicConfidentialityKind urn:oid:2.16.840.1.113883.1.11.16926 STATIC (CONF:1198-5259).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:languageCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5372">
                     <xsl:attribute name="test">count(cda:languageCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] languageCode, which SHALL be selected from ValueSet Language urn:oid:2.16.840.1.113883.1.11.11526 DYNAMIC (CONF:1198-5372).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-6380-c">
                     <xsl:attribute name="test">count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0</xsl:attribute>
                     <svrl:text>If  setId is present versionNumber *SHALL* be present (CONF:1198-6380).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-6387-c">
                     <xsl:attribute name="test">count(cda:versionNumber |cda:setId)=2 or count(cda:versionNumber | cda:setId)=0</xsl:attribute>
                     <svrl:text>If versionNumber is present setId *SHALL* be present (CONF:1198-6387).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5268">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] id (CONF:1198-5268).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5271-c">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This patientRole SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5271).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget/cda:patientRole/cda:patient) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:name))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5284-c">
                     <xsl:attribute name="test">count(cda:recordTarget/cda:patientRole/cda:patient) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:name)</xsl:attribute>
                     <svrl:text>This patient SHALL contain at least one [1..*] US Realm Patient Name (PTN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1) (CONF:1198-5284).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:administrativeGenderCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-6394">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:administrativeGenderCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] administrativeGenderCode, which SHALL be selected from ValueSet Administrative Gender (HL7 V3) urn:oid:2.16.840.1.113883.1.11.1 DYNAMIC (CONF:1198-6394).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 4)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5299-c">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 4</xsl:attribute>
                     <svrl:text>*SHALL* be precise to year (CONF:1198-5299).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:raceCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5322">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:raceCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] raceCode, which SHALL be selected from ValueSet Race Category Excluding Nulls urn:oid:2.16.840.1.113883.3.2074.1.1.3 DYNAMIC (CONF:1198-5322).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:ethnicGroupCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5323">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:ethnicGroupCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHALL contain exactly one [1..1] ethnicGroupCode, which SHALL be selected from ValueSet Ethnicity urn:oid:2.16.840.1.114222.4.11.837 DYNAMIC (CONF:1198-5323).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5386-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>This guardianPerson SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5386).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:languageCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5407">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:languageCode)=1]</xsl:attribute>
                     <svrl:text>The languageCommunication, if present, SHALL contain exactly one [1..1] languageCode, which SHALL be selected from ValueSet Language urn:oid:2.16.840.1.113883.1.11.11526 DYNAMIC (CONF:1198-5407).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/sdtc:raceCode) or cda:recordTarget/cda:patientRole/cda:patient/cda:raceCode)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-31347-c">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/sdtc:raceCode) or cda:recordTarget/cda:patientRole/cda:patient/cda:raceCode</xsl:attribute>
                     <svrl:text>If sdtc:raceCode is present, then the patient *SHALL* contain [[]1..1[]] raceCode (CONF:1198-31347).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:name) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5419">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:name) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] name (CONF:1198-5419).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5422-c">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization) or cda:recordTarget/cda:patientRole/cda:providerOrganization[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>The providerOrganization, if present, SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5422).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5445-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>Such authors SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:1198-5445).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5449">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedAuthor SHALL contain at least one [1..*] id (CONF:1198-5449).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16788">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code]</xsl:attribute>
                     <svrl:text>The code, if present, SHALL contain exactly one [1..1] @code, which SHOULD be selected from ValueSet Healthcare Provider Taxonomy (HIPAA) urn:oid:2.16.840.1.114222.4.11.1066 DYNAMIC (CONF:1198-16788).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author/cda:assignedAuthor) &lt;= count(cda:author/cda:assignedAuthor/cda:addr))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5452-c">
                     <xsl:attribute name="test">count(cda:author/cda:assignedAuthor) &lt;= count(cda:author/cda:assignedAuthor/cda:addr)</xsl:attribute>
                     <svrl:text>This assignedAuthor SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5452).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16789-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>The assignedPerson, if present, SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-16789).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:manufacturerModelName)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16784">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:manufacturerModelName)=1]</xsl:attribute>
                     <svrl:text>The assignedAuthoringDevice, if present, SHALL contain exactly one [1..1] manufacturerModelName (CONF:1198-16784).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:softwareName)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16785">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice) or cda:author/cda:assignedAuthor/cda:assignedAuthoringDevice[count(cda:softwareName)=1]</xsl:attribute>
                     <svrl:text>The assignedAuthoringDevice, if present, SHALL contain exactly one [1..1] softwareName (CONF:1198-16785).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)=1] and not(cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)!=1] ))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16790-c">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)=1] and not(cda:author/cda:assignedAuthor[count(cda:assignedPerson |cda:assignedAuthoringDevice)!=1] )</xsl:attribute>
                     <svrl:text>There *SHALL* be exactly one assignedAuthor/assignedPerson or exactly one assignedAuthor/assignedAuthoringDevice (CONF:1198-16790).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:dataEnterer/cda:assignedEntity) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:addr))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5460-c">
                     <xsl:attribute name="test">count(cda:dataEnterer/cda:assignedEntity) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:addr)</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5460).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5470-c">
                     <xsl:attribute name="test">count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson) &lt;= count(cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name)</xsl:attribute>
                     <svrl:text>This assignedPerson SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5470).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5524">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain exactly one [1..1] name (CONF:1198-5524).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:addr)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5559-c">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization[count(cda:addr)=1]</xsl:attribute>
                     <svrl:text>This representedCustodianOrganization SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5559).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient) &lt;= count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5568-c">
                     <xsl:attribute name="test">count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient) &lt;= count(cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name)</xsl:attribute>
                     <svrl:text>The informationRecipient, if present, SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5568).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization) or cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5578">
                     <xsl:attribute name="test">not(cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization) or cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHALL contain exactly one [1..1] name (CONF:1198-5578).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(existence_schema_tested))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5580-c">
                     <xsl:attribute name="test">not(existence_schema_tested)</xsl:attribute>
                     <svrl:text>The legalAuthenticator, if present, SHALL contain exactly one [1..1] US Realm Date and Time (DTM.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.4) (CONF:1198-5580).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:signatureCode) or cda:legalAuthenticator/cda:signatureCode[@code='S'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5584">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:signatureCode) or cda:legalAuthenticator/cda:signatureCode[@code='S']</xsl:attribute>
                     <svrl:text>This signatureCode SHALL contain exactly one [1..1] @code="S" (CodeSystem: HL7ParticipationSignature urn:oid:2.16.840.1.113883.5.89 STATIC) (CONF:1198-5584).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator) or cda:legalAuthenticator/cda:assignedEntity[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5589-c">
                     <xsl:attribute name="test">not(cda:legalAuthenticator) or cda:legalAuthenticator/cda:assignedEntity[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This assignedEntity SHALL contain at least one [1..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5589).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5598-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>This assignedPerson SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:1198-5598).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant) = count( cda:participant/cda:associatedEntity[cda:associatedPerson | cda:scopingOrganization]))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-10006-c">
                     <xsl:attribute name="test">count(cda:participant) = count( cda:participant/cda:associatedEntity[cda:associatedPerson | cda:scopingOrganization])</xsl:attribute>
                     <svrl:text>*SHALL* contain associatedEntity/associatedPerson *AND/OR* associatedEntity/scopingOrganization (CONF:1198-10006).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:inFulfillmentOf/cda:order) or cda:inFulfillmentOf/cda:order[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9954">
                     <xsl:attribute name="test">not(cda:inFulfillmentOf/cda:order) or cda:inFulfillmentOf/cda:order[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This order SHALL contain at least one [1..*] id (CONF:1198-9954).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:effectiveTime) or cda:documentationOf/cda:serviceEvent/cda:effectiveTime[count(cda:low)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14838">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:effectiveTime) or cda:documentationOf/cda:serviceEvent/cda:effectiveTime[count(cda:low)=1]</xsl:attribute>
                     <svrl:text>This effectiveTime SHALL contain exactly one [1..1] low (CONF:1198-14838).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[@typeCode and @typeCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.19601']/voc:code/@value])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14840">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer) or cda:documentationOf/cda:serviceEvent/cda:performer[@typeCode and @typeCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.19601']/voc:code/@value]</xsl:attribute>
                     <svrl:text>The performer, if present, SHALL contain exactly one [1..1] @typeCode, which SHALL be selected from ValueSet x_ServiceEventPerformer urn:oid:2.16.840.1.113883.1.11.19601 STATIC (CONF:1198-14840).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9959">
                     <xsl:attribute name="test">not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain at least one [1..*] id (CONF:1198-9959).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:effectiveTime)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9958">
                     <xsl:attribute name="test">not(cda:componentOf/cda:encompassingEncounter) or cda:componentOf/cda:encompassingEncounter[count(cda:effectiveTime)=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] effectiveTime (CONF:1198-9958).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32948-c">
                     <xsl:attribute name="test">.</xsl:attribute>
                     <svrl:text>This code *SHALL* be drawn from the LOINC document type ontology (LOINC codes where SCALE = DOC) (CONF:1198-32948).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e543')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']"
                 priority="64"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e543']">
            <schxslt:rule pattern="d206e543">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-83-branch-83-errors for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-83-branch-83-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e543">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-83-branch-83-errors">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:intendedRecipient)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-674-branch-83">
                     <xsl:attribute name="test">count(cda:intendedRecipient)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] intendedRecipient (CONF:3315-674).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:intendedRecipient[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-675-branch-83">
                     <xsl:attribute name="test">cda:intendedRecipient[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This intendedRecipient SHALL contain at least one [1..*] id (CONF:3315-675).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:intendedRecipient[count(cda:informationRecipient)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-676-branch-83">
                     <xsl:attribute name="test">cda:intendedRecipient[count(cda:informationRecipient)=1]</xsl:attribute>
                     <svrl:text>This intendedRecipient SHALL contain exactly one [1..1] informationRecipient (CONF:3315-676).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:intendedRecipient/cda:id[@root])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-683-branch-83">
                     <xsl:attribute name="test">cda:intendedRecipient/cda:id[@root]</xsl:attribute>
                     <svrl:text>Such ids SHALL contain exactly one [1..1] @root (CONF:3315-683).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:intendedRecipient[count(cda:addr)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-685-branch-83-c">
                     <xsl:attribute name="test">cda:intendedRecipient[count(cda:addr)=1]</xsl:attribute>
                     <svrl:text>This intendedRecipient SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-685).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:intendedRecipient[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-686-branch-83">
                     <xsl:attribute name="test">cda:intendedRecipient[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This intendedRecipient SHALL contain at least one [1..*] telecom (CONF:3315-686).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:intendedRecipient/cda:informationRecipient[count(cda:name) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-687-branch-83-c">
                     <xsl:attribute name="test">cda:intendedRecipient/cda:informationRecipient[count(cda:name) &gt; 0]</xsl:attribute>
                     <svrl:text>This informationRecipient SHALL contain at least one [1..*] US Realm Person Name (PN.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.1.1) (CONF:3315-687).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:name) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-689-branch-83">
                     <xsl:attribute name="test">not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:name) &gt; 0]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHALL contain at least one [1..*] name (CONF:3315-689).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:addr)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-691-branch-83-c">
                     <xsl:attribute name="test">not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:addr)=1]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHALL contain exactly one [1..1] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:3315-691).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e543')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]"
                 priority="63"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1054']">
            <schxslt:rule pattern="d206e1054">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-errors for context "cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-errors">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1054">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-errors">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-84">
                     <xsl:attribute name="test">count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] entry (CONF:3315-84) such that it SHALL contain exactly one [1..1] Reportability Response Subject (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.7:2017-04-01) (CONF:3315-161).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-85">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-85) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.2.1" (CONF:3315-91). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-92).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-86">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-86).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='88084-9'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-93">
                     <xsl:attribute name="test">cda:code[@code='88084-9']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="88084-9" Reportable condition response information and summary Document (CONF:3315-93).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-94">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.1']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.1" (CodeSystem: LOINC urn:oid:2.16.840.1.113883.6.1) (CONF:3315-94).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:text)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-95">
                     <xsl:attribute name="test">count(cda:text)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] text (CONF:3315-95).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1054')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]"
                 priority="62"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1079']">
            <schxslt:rule pattern="d206e1079">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-errors for context "cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-errors">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1079">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-errors">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-103">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-103) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.2.2" (CONF:3315-109). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-110).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-104">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-104).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:text)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-105">
                     <xsl:attribute name="test">count(cda:text)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] text (CONF:3315-105).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-108">
                     <xsl:attribute name="test">count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] entry (CONF:3315-108) such that it SHALL contain exactly one [1..1] Reportability Response Summary (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.8:2017-04-01) (CONF:3315-176).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='55112-7'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-111">
                     <xsl:attribute name="test">cda:code[@code='55112-7']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="55112-7" Document Summary (CONF:3315-111).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-112">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.1']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.1" (CodeSystem: LOINC urn:oid:2.16.840.1.113883.6.1) (CONF:3315-112).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entry[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-613">
                     <xsl:attribute name="test">count(cda:entry[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] entry (CONF:3315-613) such that it SHALL contain exactly one [1..1] Reportability Response Priority (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.30:2017-04-01) (CONF:3315-614).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entry[count(cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-705">
                     <xsl:attribute name="test">count(cda:entry[count(cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] entry (CONF:3315-705) such that it SHALL contain exactly one [1..1] Reportability Response Coded Information Organizer (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.34:2017-04-01) (CONF:3315-706).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1079')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]"
                 priority="61"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1111']">
            <schxslt:rule pattern="d206e1111">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-errors for context "cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-errors">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1111">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-errors">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-121">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-121) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.2.3" (CONF:3315-127). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-128).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-122">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-122).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-126">
                     <xsl:attribute name="test">count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] entry (CONF:3315-126) such that it SHALL contain exactly one [1..1] Received eICR Information (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.9:2017-04-01) (CONF:3315-203).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='88082-3'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-129">
                     <xsl:attribute name="test">cda:code[@code='88082-3']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="88082-3" Initial case report processing information Document (CONF:3315-129).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-130">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.1']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.1" (CodeSystem: LOINC urn:oid:2.16.840.1.113883.6.1) (CONF:3315-130).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-466">
                     <xsl:attribute name="test">count(cda:entry[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] entry (CONF:3315-466) such that it SHALL contain exactly one [1..1] eICR Processing Status (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.29:2017-04-01) (CONF:3315-467).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1111')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]"
                 priority="60"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1136']">
            <schxslt:rule pattern="d206e1136">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-errors for context "cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-errors">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1136">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-errors">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-131">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-131) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.34" (CONF:3315-137). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-138).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-132">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-132).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR11'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-139">
                     <xsl:attribute name="test">cda:code[@code='RR11']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR11" Reportability Response Coded Information (CONF:3315-139).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-140">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-140).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:component[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']])=1]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-703">
                     <xsl:attribute name="test">count(cda:component[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']])=1]) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] component (CONF:3315-703) such that it SHALL contain exactly one [1..1] Relevant Reportable Condition Observation (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.12:2017-04-01) (CONF:3315-704).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='CLUSTER')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-707">
                     <xsl:attribute name="test">@classCode='CLUSTER'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="CLUSTER" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-707).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-708">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-708).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:statusCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-709">
                     <xsl:attribute name="test">count(cda:statusCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] statusCode (CONF:3315-709).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:statusCode[@code='completed'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-710">
                     <xsl:attribute name="test">cda:statusCode[@code='completed']</xsl:attribute>
                     <svrl:text>This statusCode SHALL contain exactly one [1..1] @code="completed" (CodeSystem: HL7ActStatus urn:oid:2.16.840.1.113883.5.14) (CONF:3315-710).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1136')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]"
                 priority="59"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1170']">
            <schxslt:rule pattern="d206e1170">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1170">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-148">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-148).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='INT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-149">
                     <xsl:attribute name="test">@moodCode='INT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="INT" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-149).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-152">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-152).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='131195008'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-153">
                     <xsl:attribute name="test">cda:code[@code='131195008']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="131195008" Subject of information (CONF:3315-153).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.96'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-154">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.96']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.96" (CodeSystem: SNOMED CT urn:oid:2.16.840.1.113883.6.96) (CONF:3315-154).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-155">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:3315-155).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:text)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-156">
                     <xsl:attribute name="test">count(cda:text)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] text (CONF:3315-156).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:id[@root])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-159">
                     <xsl:attribute name="test">cda:id[@root]</xsl:attribute>
                     <svrl:text>This id SHALL contain exactly one [1..1] @root (CONF:3315-159).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7391">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:1098-7391).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='INT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7392">
                     <xsl:attribute name="test">@moodCode='INT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="INT" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:1098-7392).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-16884">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet Patient Education urn:oid:2.16.840.1.113883.11.20.9.34 DYNAMIC (CONF:1098-16884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:statusCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7396">
                     <xsl:attribute name="test">count(cda:statusCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] statusCode (CONF:1098-7396).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:statusCode[@code='completed'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-19106">
                     <xsl:attribute name="test">cda:statusCode[@code='completed']</xsl:attribute>
                     <svrl:text>This statusCode SHALL contain exactly one [1..1] @code="completed" Completed (CodeSystem: HL7ActStatus urn:oid:2.16.840.1.113883.5.14 STATIC) (CONF:1098-19106).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-146">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-146) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.7" (CONF:3315-150). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-151).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1170')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]"
                 priority="58"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1222']">
            <schxslt:rule pattern="d206e1222">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1222">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-163">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-163).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-164">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:3315-164).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:text)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-165">
                     <xsl:attribute name="test">count(cda:text)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] text (CONF:3315-165).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-170">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-170).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='INT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-171">
                     <xsl:attribute name="test">@moodCode='INT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="INT" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-171).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='304561000'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-172">
                     <xsl:attribute name="test">cda:code[@code='304561000']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="304561000" Informing health care professional (procedure) (CONF:3315-172).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.96'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-173">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.96']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.96" (CodeSystem: SNOMED CT urn:oid:2.16.840.1.113883.6.96) (CONF:3315-173).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:id[@root])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-174">
                     <xsl:attribute name="test">cda:id[@root]</xsl:attribute>
                     <svrl:text>This id SHALL contain exactly one [1..1] @root (CONF:3315-174).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7391">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:1098-7391).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='INT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7392">
                     <xsl:attribute name="test">@moodCode='INT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="INT" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:1098-7392).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-16884">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet Patient Education urn:oid:2.16.840.1.113883.11.20.9.34 DYNAMIC (CONF:1098-16884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:statusCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-7396">
                     <xsl:attribute name="test">count(cda:statusCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] statusCode (CONF:1098-7396).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:statusCode[@code='completed'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-19106">
                     <xsl:attribute name="test">cda:statusCode[@code='completed']</xsl:attribute>
                     <svrl:text>This statusCode SHALL contain exactly one [1..1] @code="completed" Completed (CodeSystem: HL7ActStatus urn:oid:2.16.840.1.113883.5.14 STATIC) (CONF:1098-19106).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-162">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-162) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.8" (CONF:3315-168). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-169).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1222')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]"
                 priority="57"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1274']">
            <schxslt:rule pattern="d206e1274">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1274">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-178">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-178).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-179">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:3315-179).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-185">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-185).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-186">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-186).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR5'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-187">
                     <xsl:attribute name="test">cda:code[@code='RR5']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR5" Received eICR Information (CONF:3315-187).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-188">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-188).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:id[@root])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-189">
                     <xsl:attribute name="test">cda:id[@root]</xsl:attribute>
                     <svrl:text>This id SHALL contain exactly one [1..1] @root (CONF:3315-189).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:reference)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-190">
                     <xsl:attribute name="test">count(cda:reference)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] reference (CONF:3315-190).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:reference[@typeCode='REFR'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-191">
                     <xsl:attribute name="test">cda:reference[@typeCode='REFR']</xsl:attribute>
                     <svrl:text>This reference SHALL contain exactly one [1..1] @typeCode="REFR" Refers to (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-191).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:reference[count(cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-192">
                     <xsl:attribute name="test">cda:reference[count(cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']])=1]</xsl:attribute>
                     <svrl:text>This reference SHALL contain exactly one [1..1] eICR External Document Reference (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.10:2017-04-01) (CONF:3315-192).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:effectiveTime)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-432">
                     <xsl:attribute name="test">count(cda:effectiveTime)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] effectiveTime (CONF:3315-432).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-177">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-177) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.9" (CONF:3315-183). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-184).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1274')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]"
                 priority="56"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1318']">
            <schxslt:rule pattern="d206e1318">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-errors for context "cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-errors">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1318">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-errors">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-193">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-193) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.10" (CONF:3315-197). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-198).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='DOCCLIN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-194">
                     <xsl:attribute name="test">@classCode='DOCCLIN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="DOCCLIN" Clinical Document (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-194).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-195">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-195).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-196">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-196).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='55751-2'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-199">
                     <xsl:attribute name="test">cda:code[@code='55751-2']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="55751-2" Public Health Case Report (eICR) (CONF:3315-199).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-200">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.1']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.1" (CodeSystem: LOINC urn:oid:2.16.840.1.113883.6.1) (CONF:3315-200).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-433">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:3315-433).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:setId)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-737">
                     <xsl:attribute name="test">count(cda:setId)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] setId (CONF:3315-737).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-738">
                     <xsl:attribute name="test">count(cda:versionNumber)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] versionNumber (CONF:3315-738).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='DOCCLIN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-31931">
                     <xsl:attribute name="test">@classCode='DOCCLIN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="DOCCLIN" Clinical Document (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:1098-31931).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-31932">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:1098-31932).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-31933">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:1098-31933).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115'][@extension='2014-06-09'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32748">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115'][@extension='2014-06-09'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:1098-32748) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.22.4.115" (CONF:1098-32750). SHALL contain exactly one [1..1] @extension="2014-06-09" (CONF:1098-32749).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32751">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:1098-32751).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1318')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]"
                 priority="55"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1371']">
            <schxslt:rule pattern="d206e1371">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1371">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-217">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-217) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.12" (CONF:3315-225). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-226).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-233">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-233).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-234">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-234).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-434">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-434).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entryRelationship[count(cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']])=1]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-548">
                     <xsl:attribute name="test">count(cda:entryRelationship[count(cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']])=1]) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] entryRelationship (CONF:3315-548) such that it SHALL contain exactly one [1..1] Reportability Information Organizer (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.13:2017-04-01) (CONF:3315-550).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value[@codeSystem='2.16.840.1.113883.6.96' or @nullFlavor][@xsi:type='CD'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-552">
                     <xsl:attribute name="test">count(cda:value[@codeSystem='2.16.840.1.113883.6.96' or @nullFlavor][@xsi:type='CD'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value with @xsi:type="CD", where the code SHALL be selected from CodeSystem SNOMED CT (urn:oid:2.16.840.1.113883.6.96) DYNAMIC (CONF:3315-552).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[count(cda:translation)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-553">
                     <xsl:attribute name="test">cda:code[count(cda:translation)=1]</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] translation (CONF:3315-553).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='64572001'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-554">
                     <xsl:attribute name="test">cda:code[@code='64572001']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="64572001" Condition (CONF:3315-554).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.113883.6.96'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-555">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.113883.6.96']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.96" (CodeSystem: SNOMED CT urn:oid:2.16.840.1.113883.6.96) (CONF:3315-555).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code/cda:translation[@code='75323-6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-556">
                     <xsl:attribute name="test">cda:code/cda:translation[@code='75323-6']</xsl:attribute>
                     <svrl:text>This translation SHALL contain exactly one [1..1] @code="75323-6" Condition (CONF:3315-556).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code/cda:translation[@codeSystem='2.16.840.1.113883.6.1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-557">
                     <xsl:attribute name="test">cda:code/cda:translation[@codeSystem='2.16.840.1.113883.6.1']</xsl:attribute>
                     <svrl:text>This translation SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.113883.6.1" (CodeSystem: LOINC urn:oid:2.16.840.1.113883.6.1) (CONF:3315-557).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:value[@nullFlavor] or cda:value[@code][@codeSystem][@displayName])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-736-c">
                     <xsl:attribute name="test">cda:value[@nullFlavor] or cda:value[@code][@codeSystem][@displayName]</xsl:attribute>
                     <svrl:text>If @code is present then @codeSystem and @displayName must both be present (CONF:3315-736).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1371')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]"
                 priority="54"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1415']">
            <schxslt:rule pattern="d206e1415">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-errors for context "cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-errors">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1415">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-errors">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-237">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-237) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.13" (CONF:3315-239). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-240).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:component[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-238">
                     <xsl:attribute name="test">count(cda:component[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] component (CONF:3315-238) such that it SHALL contain exactly one [1..1] Determination of Reportability (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.19:2017-04-01) (CONF:3315-329).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='CLUSTER')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-241">
                     <xsl:attribute name="test">@classCode='CLUSTER'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="CLUSTER" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-241).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-242">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-242).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:statusCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-245">
                     <xsl:attribute name="test">count(cda:statusCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] statusCode (CONF:3315-245).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:statusCode[@code='completed'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-246">
                     <xsl:attribute name="test">cda:statusCode[@code='completed']</xsl:attribute>
                     <svrl:text>This statusCode SHALL contain exactly one [1..1] @code="completed" (CodeSystem: HL7ActStatus urn:oid:2.16.840.1.113883.5.14) (CONF:3315-246).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-429">
                     <xsl:attribute name="test">count(cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] Rules Authoring Agency (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.4.3:2017-04-01) (CONF:3315-429).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-543">
                     <xsl:attribute name="test">count(cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] Routing Entity (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.4.1:2017-04-01) (CONF:3315-543).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-581">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHALL be selected from ValueSet Location Relevance urn:oid:2.16.840.1.113883.10.20.15.2.5.6 DYNAMIC (CONF:3315-581).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1415')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]"
                 priority="53"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1449']">
            <schxslt:rule pattern="d206e1449">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1449">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-249">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-249) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.14" (CONF:3315-251). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-252).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-250">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-250).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR4'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-253">
                     <xsl:attribute name="test">cda:code[@code='RR4']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR4" Timeframe to report (urgency) (CONF:3315-253).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-254">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-254).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value[@xsi:type='PQ'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-255">
                     <xsl:attribute name="test">count(cda:value[@xsi:type='PQ'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value with @xsi:type="PQ" (CONF:3315-255).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-256">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-256).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-257">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-257).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:value[@xsi:type='PQ'][@value])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-671">
                     <xsl:attribute name="test">cda:value[@xsi:type='PQ'][@value]</xsl:attribute>
                     <svrl:text>This value SHALL contain exactly one [1..1] @value (CONF:3315-671).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:value[@xsi:type='PQ'][@unit])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-672">
                     <xsl:attribute name="test">cda:value[@xsi:type='PQ'][@unit]</xsl:attribute>
                     <svrl:text>This value SHALL contain exactly one [1..1] @unit, which SHOULD be selected from CodeSystem UCUM (urn:oid:2.16.840.1.113883.6.8) DYNAMIC (CONF:3315-672).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1449')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]"
                 priority="52"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1483']">
            <schxslt:rule pattern="d206e1483">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-errors for context "cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-errors">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1483">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-errors">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-271">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-271) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.17" (CONF:3315-274). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-275).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-272">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-272).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='DOC')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-276">
                     <xsl:attribute name="test">@classCode='DOC'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="DOC" Document (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-276).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-277">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-277).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:text) or cda:text[count(cda:reference)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-280">
                     <xsl:attribute name="test">not(cda:text) or cda:text[count(cda:reference)=1]</xsl:attribute>
                     <svrl:text>The text, if present, SHALL contain exactly one [1..1] reference (CONF:3315-280).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[count(cda:originalText)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-281">
                     <xsl:attribute name="test">cda:code[count(cda:originalText)=1]</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] originalText (CONF:3315-281).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@nullFlavor='OTH'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-285">
                     <xsl:attribute name="test">cda:code[@nullFlavor='OTH']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @nullFlavor="OTH" (CodeSystem: HL7NullFlavor urn:oid:2.16.840.1.113883.5.1008) (CONF:3315-285).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1483')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]"
                 priority="51"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1511']">
            <schxslt:rule pattern="d206e1511">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1511">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-347">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-347) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.19" (CONF:3315-349). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-350).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-348">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-348).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR1'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-351">
                     <xsl:attribute name="test">cda:code[@code='RR1']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR1" Determination of reportability (CONF:3315-351).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-352">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-352).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value[@xsi:type='CD' and @code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.10.20.15.2.5.3']/voc:code/@value or @nullFlavor])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-353">
                     <xsl:attribute name="test">count(cda:value[@xsi:type='CD' and @code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.10.20.15.2.5.3']/voc:code/@value or @nullFlavor])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value with @xsi:type="CD", where the code SHALL be selected from ValueSet Determination of Reportability urn:oid:2.16.840.1.113883.10.20.15.2.5.3 STATIC 2017-02-01 (CONF:3315-353).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-354">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-354).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-355">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-355).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1511')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]"
                 priority="50"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1511']">
            <schxslt:rule pattern="d206e1511">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-533-branch-533-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-533-branch-533-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1511">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-533-branch-533-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@typeCode='RSON')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-535-branch-533">
                     <xsl:attribute name="test">@typeCode='RSON'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @typeCode="RSON" Reason (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-535).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1511')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]"
                 priority="49"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1511']">
            <schxslt:rule pattern="d206e1511">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-534-branch-534-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-534-branch-534-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1511">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-534-branch-534-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]/cda:entryRelationship[cda:observation]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@typeCode='RSON')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-537-branch-534">
                     <xsl:attribute name="test">@typeCode='RSON'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @typeCode="RSON" Reason (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-537).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1511')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]"
                 priority="48"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1551']">
            <schxslt:rule pattern="d206e1551">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-errors for context "cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-errors">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1551">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-errors">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-387">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-387) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.4.1" (CONF:3315-389). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-390).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@typeCode='LOC')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-388">
                     <xsl:attribute name="test">@typeCode='LOC'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @typeCode="LOC" Location (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-388).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participantRole)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-391">
                     <xsl:attribute name="test">count(cda:participantRole)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] participantRole (CONF:3315-391).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:playingEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-393">
                     <xsl:attribute name="test">cda:participantRole[count(cda:playingEntity)=1]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain exactly one [1..1] playingEntity (CONF:3315-393).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:playingEntity[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-399">
                     <xsl:attribute name="test">cda:participantRole/cda:playingEntity[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This playingEntity SHALL contain exactly one [1..1] name (CONF:3315-399).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-392">
                     <xsl:attribute name="test">cda:participantRole[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain exactly one [1..1] code (CONF:3315-392).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:code[@code='RR7'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-395">
                     <xsl:attribute name="test">cda:participantRole/cda:code[@code='RR7']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR7" Routing Enitity (CONF:3315-395).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-396">
                     <xsl:attribute name="test">cda:participantRole/cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-396).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1551')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]"
                 priority="47"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1583']">
            <schxslt:rule pattern="d206e1583">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-errors for context "cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-errors">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1583">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-errors">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-401">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-401) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.4.2" (CONF:3315-405). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-406).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participantRole)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-402">
                     <xsl:attribute name="test">count(cda:participantRole)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] participantRole (CONF:3315-402).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:playingEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-404">
                     <xsl:attribute name="test">cda:participantRole[count(cda:playingEntity)=1]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain exactly one [1..1] playingEntity (CONF:3315-404).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@typeCode='LOC')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-407">
                     <xsl:attribute name="test">@typeCode='LOC'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @typeCode="LOC" Location (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-407).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:playingEntity[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-410">
                     <xsl:attribute name="test">cda:participantRole/cda:playingEntity[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This playingEntity SHALL contain exactly one [1..1] name (CONF:3315-410).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-413">
                     <xsl:attribute name="test">cda:participantRole[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain at least one [1..*] addr (CONF:3315-413).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-414">
                     <xsl:attribute name="test">cda:participantRole[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain at least one [1..*] telecom (CONF:3315-414).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-403">
                     <xsl:attribute name="test">cda:participantRole[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain exactly one [1..1] code (CONF:3315-403).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:code[@code='RR8'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-408">
                     <xsl:attribute name="test">cda:participantRole/cda:code[@code='RR8']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR8" Responsible Agency (CONF:3315-408).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-409">
                     <xsl:attribute name="test">cda:participantRole/cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-409).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1583')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]"
                 priority="46"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1620']">
            <schxslt:rule pattern="d206e1620">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-errors for context "cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-errors">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1620">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-errors">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-415">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-415) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.4.3" (CONF:3315-419). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-420).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participantRole)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-416">
                     <xsl:attribute name="test">count(cda:participantRole)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] participantRole (CONF:3315-416).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:playingEntity)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-418">
                     <xsl:attribute name="test">cda:participantRole[count(cda:playingEntity)=1]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain exactly one [1..1] playingEntity (CONF:3315-418).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:playingEntity[count(cda:name)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-423">
                     <xsl:attribute name="test">cda:participantRole/cda:playingEntity[count(cda:name)=1]</xsl:attribute>
                     <svrl:text>This playingEntity SHALL contain exactly one [1..1] name (CONF:3315-423).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-426">
                     <xsl:attribute name="test">cda:participantRole[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain at least one [1..*] addr (CONF:3315-426).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-427">
                     <xsl:attribute name="test">cda:participantRole[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain at least one [1..*] telecom (CONF:3315-427).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@typeCode='LOC')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-428">
                     <xsl:attribute name="test">@typeCode='LOC'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @typeCode="LOC" Location (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-428).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-417">
                     <xsl:attribute name="test">cda:participantRole[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This participantRole SHALL contain exactly one [1..1] code (CONF:3315-417).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:code[@code='RR12'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-421">
                     <xsl:attribute name="test">cda:participantRole/cda:code[@code='RR12']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR12" Rules Authoring Agency (CONF:3315-421).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole/cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-422">
                     <xsl:attribute name="test">cda:participantRole/cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-422).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1620')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]"
                 priority="45"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1657']">
            <schxslt:rule pattern="d206e1657">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1657">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-435">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-435) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.20" (CONF:3315-440). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-450).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-436">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHALL be selected from ValueSet External Resource Type urn:oid:2.16.840.1.113883.10.20.15.2.5.4 DYNAMIC (CONF:3315-436).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:reference) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-438">
                     <xsl:attribute name="test">count(cda:reference) &gt; 0</xsl:attribute>
                     <svrl:text>SHALL contain at least one [1..*] reference (CONF:3315-438).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:reference[@typeCode='REFR'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-444">
                     <xsl:attribute name="test">cda:reference[@typeCode='REFR']</xsl:attribute>
                     <svrl:text>Such references SHALL contain exactly one [1..1] @typeCode="REFR" refers to (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-444).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-448">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-448).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-449">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-449).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:reference[count(cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-451">
                     <xsl:attribute name="test">cda:reference[count(cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']])=1]</xsl:attribute>
                     <svrl:text>Such references SHALL contain exactly one [1..1] External Reference (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.17:2017-04-01) (CONF:3315-451).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:priorityCode)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-454">
                     <xsl:attribute name="test">count(cda:priorityCode)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] priorityCode (CONF:3315-454).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:id)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-597">
                     <xsl:attribute name="test">count(cda:id)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] id (CONF:3315-597).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:priorityCode[not(@nullFlavor)])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-626">
                     <xsl:attribute name="test">cda:priorityCode[not(@nullFlavor)]</xsl:attribute>
                     <svrl:text>This priorityCode SHALL NOT contain [0..0] @nullFlavor (CONF:3315-626).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:priorityCode[@code])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-627">
                     <xsl:attribute name="test">cda:priorityCode[@code]</xsl:attribute>
                     <svrl:text>This priorityCode SHALL contain exactly one [1..1] @code, which SHALL be selected from ValueSet Reportability Priority urn:oid:2.16.840.1.113883.10.20.15.2.5.5 DYNAMIC (CONF:3315-627).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1657')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]"
                 priority="44"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1697']">
            <schxslt:rule pattern="d206e1697">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1697">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-456">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-456) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.22" (CONF:3315-458). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-459).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-460">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-460).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-462">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-462).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-463">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-463).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='PHC1464'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-464">
                     <xsl:attribute name="test">cda:code[@code='PHC1464']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="PHC1464" Manually Initiated eICR (CONF:3315-464).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.274'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-465">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.274']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.274" (CodeSystem: PHIN VS (CDC Local Coding System)  urn:oid:2.16.840.1.114222.4.5.274) (CONF:3315-465).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1697')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]"
                 priority="43"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1722']">
            <schxslt:rule pattern="d206e1722">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1722">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-468">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-468) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.21" (CONF:3315-470). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-471).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-469">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-469).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-472">
                     <xsl:attribute name="test">cda:code[@code='RR6']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR6" eICR processing status reason (CONF:3315-472).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-473">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-473).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-474">
                     <xsl:attribute name="test">count(cda:value)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value, which SHALL be selected from ValueSet eICR Processing Status Reason urn:oid:2.16.840.1.113883.10.20.15.2.5.7 DYNAMIC (CONF:3315-474).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-475">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-475).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-476">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-476).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:entryRelationship) or cda:entryRelationship[@typeCode='RSON'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-668">
                     <xsl:attribute name="test">not(cda:entryRelationship) or cda:entryRelationship[@typeCode='RSON']</xsl:attribute>
                     <svrl:text>The entryRelationship, if present, SHALL contain exactly one [1..1] @typeCode="RSON" Has reason (CodeSystem: HL7ActRelationshipType urn:oid:2.16.840.1.113883.5.1002) (CONF:3315-668).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:entryRelationship) or cda:entryRelationship[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-669">
                     <xsl:attribute name="test">not(cda:entryRelationship) or cda:entryRelationship[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']])=1]</xsl:attribute>
                     <svrl:text>The entryRelationship, if present, SHALL contain exactly one [1..1] eICR Processing Status Reason Detail (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.32:2017-04-01) (CONF:3315-669).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1722')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]"
                 priority="42"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1756']">
            <schxslt:rule pattern="d206e1756">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1756">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-514">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-514) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.26" (CONF:3315-517). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-518).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-515">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-515).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR2'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-519">
                     <xsl:attribute name="test">cda:code[@code='RR2']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR2" Determination of Reportability Reason (CONF:3315-519).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-520">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-520).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-521">
                     <xsl:attribute name="test">count(cda:value)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value (CONF:3315-521).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-522">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-522).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-523">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-523).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1756')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]"
                 priority="41"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1785']">
            <schxslt:rule pattern="d206e1785">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1785">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-524">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-524) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.27" (CONF:3315-526). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-527).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-525">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-525).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR3'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-528">
                     <xsl:attribute name="test">cda:code[@code='RR3']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR3" Determination of reportability rule (CONF:3315-528).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-529">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-529).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-530">
                     <xsl:attribute name="test">count(cda:value)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value (CONF:3315-530).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-531">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-531).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-532">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-532).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1785')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]"
                 priority="40"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1813']">
            <schxslt:rule pattern="d206e1813">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-errors for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1813">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-errors">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-568">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-568) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.29" (CONF:3315-570). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-571).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.10.20.15.2.5.8']/voc:code/@value or @nullFlavor])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-569">
                     <xsl:attribute name="test">count(cda:code[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.10.20.15.2.5.8']/voc:code/@value or @nullFlavor])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHALL be selected from ValueSet eICR Processing Status urn:oid:2.16.840.1.113883.10.20.15.2.5.8 STATIC 2017-02-01 (CONF:3315-569).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='ACT')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-574">
                     <xsl:attribute name="test">@classCode='ACT'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="ACT" (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-574).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-575">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-575).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not((count(cda:code[@code='RRVS19'])=0 and count(cda:entryRelationship/cda:observation/cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21'])&gt;0) or (count(cda:code[@code='RRVS19'])=1 and count(cda:entryRelationship/cda:observation/cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21'])=0))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-670-c">
                     <xsl:attribute name="test">(count(cda:code[@code='RRVS19'])=0 and count(cda:entryRelationship/cda:observation/cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21'])&gt;0) or (count(cda:code[@code='RRVS19'])=1 and count(cda:entryRelationship/cda:observation/cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21'])=0)</xsl:attribute>
                     <svrl:text>The eICR Processing Reason *SHALL* be present if the eICR CDA document was either not processed or was processed with a warning and *SHALL NOT* be present if the eICR CDA document was processed with no warnings or errors (CONF:3315-670).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1813')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]"
                 priority="39"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1834']">
            <schxslt:rule pattern="d206e1834">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1834">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-602">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-602) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.30" (CONF:3315-607). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-612).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-603">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-603).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-605">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-605).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-606">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-606).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR9'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-609">
                     <xsl:attribute name="test">cda:code[@code='RR9']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR9" Reportability Priority (CONF:3315-609).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-610">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-610).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value[@xsi:type='CD'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-611">
                     <xsl:attribute name="test">count(cda:value[@xsi:type='CD'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value with @xsi:type="CD", where the code SHALL be selected from ValueSet Reportability Priority urn:oid:2.16.840.1.113883.10.20.15.2.5.5 DYNAMIC (CONF:3315-611).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1834')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]"
                 priority="38"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1862']">
            <schxslt:rule pattern="d206e1862">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1862">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-658">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-658) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.32" (CONF:3315-660). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-661).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-659">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet eICR Processing Status Reason Detail Type urn:oid:2.16.840.1.113883.10.20.15.2.3.32 DYNAMIC (CONF:3315-659).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-664">
                     <xsl:attribute name="test">count(cda:value)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value (CONF:3315-664).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-665">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6 STATIC) (CONF:3315-665).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-666">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" Event (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001 STATIC) (CONF:3315-666).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1862')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]"
                 priority="37"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1883']">
            <schxslt:rule pattern="d206e1883">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-errors for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1883">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-errors">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33'][@extension='2017-04-01'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-718">
                     <xsl:attribute name="test">count(cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33'][@extension='2017-04-01'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] templateId (CONF:3315-718) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.10.20.15.2.3.33" (CONF:3315-721). SHALL contain exactly one [1..1] @extension="2017-04-01" (CONF:3315-722).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@classCode='OBS')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-719">
                     <xsl:attribute name="test">@classCode='OBS'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @classCode="OBS" Observation (CodeSystem: HL7ActClass urn:oid:2.16.840.1.113883.5.6) (CONF:3315-719).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(@moodCode='EVN')">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-720">
                     <xsl:attribute name="test">@moodCode='EVN'</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] @moodCode="EVN" (CodeSystem: HL7ActMood urn:oid:2.16.840.1.113883.5.1001) (CONF:3315-720).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-723">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-723).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@code='RR10'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-724">
                     <xsl:attribute name="test">cda:code[@code='RR10']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @code="RR10" eICR Validation Output (CONF:3315-724).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:code[@codeSystem='2.16.840.1.114222.4.5.232'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-725">
                     <xsl:attribute name="test">cda:code[@codeSystem='2.16.840.1.114222.4.5.232']</xsl:attribute>
                     <svrl:text>This code SHALL contain exactly one [1..1] @codeSystem="2.16.840.1.114222.4.5.232" (CodeSystem: PHIN Questions urn:oid:2.16.840.1.114222.4.5.232) (CONF:3315-725).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:value[@xsi:type='ED'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-726">
                     <xsl:attribute name="test">count(cda:value[@xsi:type='ED'])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] value with @xsi:type="ED" (CONF:3315-726).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1883')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name"
                 priority="36"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1911']">
            <schxslt:rule pattern="d206e1911">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.1-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1911">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:assignedPerson/cda:name</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1911')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr"
                 priority="35"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1920']">
            <schxslt:rule pattern="d206e1920">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.2-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.2-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1920">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.2-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:supply[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.18' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2014-06-09']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.2.3.4']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:author/cda:assignedAuthor/cda:addr | cda:participant[cda:templateId[@root='2.16.840.1.113883.10.14.34' and @extension='2014-27-10']]/cda:associatedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://icHeader.abc']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:addr | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.61' and @extension='2015-08-01']]/cda:performer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:location/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility/cda:serviceProviderOrganization/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:performer[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.1' and @extension='2017-08-01']]/cda:assignedEntity/cda:representedOrganization/cda:addr | cda:author[cda:templateId[@root='2.16.840.1.113883.10.20.37.4.2' and @extension='2017-08-01']]/cda:assignedAuthor/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:addr | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='https://mytest.Header123']]/cda:recordTarget/cda:patientRole/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:addr | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:receivedOrganization/cda:addr</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@use)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7290">
                     <xsl:attribute name="test">@use</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet PostalAddressUse urn:oid:2.16.840.1.113883.1.11.10637 STATIC 2005-05-01 (CONF:81-7290).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:state)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7293">
                     <xsl:attribute name="test">count(cda:state)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] state (ValueSet: StateValueSet urn:oid:2.16.840.1.113883.3.88.12.80.1 DYNAMIC) (CONF:81-7293).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested_here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7294-c">
                     <xsl:attribute name="test">not(tested_here)</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] postalCode, which SHOULD be selected from ValueSet PostalCode urn:oid:2.16.840.1.113883.3.88.12.80.2 DYNAMIC (CONF:81-7294).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:country)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-7295">
                     <xsl:attribute name="test">count(cda:country)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] country, which SHALL be selected from ValueSet Country urn:oid:2.16.840.1.113883.3.88.12.80.63 DYNAMIC (CONF:81-7295).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1920')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name"
                 priority="34"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1938']">
            <schxslt:rule pattern="d206e1938">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1938">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.1.1-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2014-06-09']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.123']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounterParticipant[cda:templateId[@root='2.16.840.1.113883.10.20.6.2.2' and @extension='2014-06-09']]/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2014-06-09']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.26' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.25' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2014-08-08']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:procedure[cda:templateId[@root='2.16.840.1.113883.10.13.15' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:encounter[cda:templateId[@root='2.16.840.1.113883.10.13.20' and @extension='2014-08-08']]/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-11-19']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2014-12-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:componentOf/cda:encompassingEncounter/cda:encounterParticipant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.13.1' and @extension='2015-01-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2015-08-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.14' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.5' and @extension='2015-08-01']]/cda:participant/cda:associatedEntity/cda:associatedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-01-22']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-02-08']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:guardianPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:assignedAuthor/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:dataEnterer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informant/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-10-05']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.202' and @extension='2016-11-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.15' and @extension='2016-11-29']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:componentOf/cda:encompassingEncounter/cda:responsibleParty/cda:assignedEntity/cda:assignedPerson/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:recordTarget/cda:patientRole/cda:patient/cda:name | cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.48' and @extension='2017-05-01']]/cda:participant/cda:participantRole/cda:playingEntity/cda:name | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1938')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime"
                 priority="33"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1946']">
            <schxslt:rule pattern="d206e1946">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-oid-2.16.840.1.113883.10.20.22.5.4-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-oid-2.16.840.1.113883.10.20.22.5.4-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1946">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-oid-2.16.840.1.113883.10.20.22.5.4-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2014-06-09']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2015-07-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='1.3.6.1.4.1.19376.1.7.3.1.1.19.1.1' and @extension='2014-11-03']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-11-02']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='20160422']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2016-03-01']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:legalAuthenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:authenticator/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.9999' and @extension='2016-03-23']]/cda:effectiveTime | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2' and @extension='2016-12-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:author/cda:time | cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.24.1.3' and @extension='2017-07-01']]/cda:effectiveTime</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(string-length(@value)&gt;=12)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-10128-c">
                     <xsl:attribute name="test">string-length(@value)&gt;=12</xsl:attribute>
                     <svrl:text>*SHOULD* be precise to the minute (CONF:81-10128).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(string-length(@value)&lt;10 or ( string-length(@value)&gt;=10 and (contains(@value,'+') or contains(@value,'-'))))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-81-10130-c">
                     <xsl:attribute name="test">string-length(@value)&lt;10 or ( string-length(@value)&gt;=10 and (contains(@value,'+') or contains(@value,'-')))</xsl:attribute>
                     <svrl:text>If more precise than day, *SHOULD* include time-zone offset (CONF:81-10130).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1946')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]"
                 priority="32"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1958']">
            <schxslt:rule pattern="d206e1958">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1958">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.20-2014-06-09-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.20' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-16884-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet Patient Education urn:oid:2.16.840.1.113883.11.20.9.34 DYNAMIC (CONF:1098-16884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1958')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]"
                 priority="31"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1967']">
            <schxslt:rule pattern="d206e1967">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-warnings for context "cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-warnings">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1967">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.4.115-2014-06-09-warnings">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.115' and @extension='2014-06-09']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:setId)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32752">
                     <xsl:attribute name="test">count(cda:setId)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] setId (CONF:1098-32752).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32753">
                     <xsl:attribute name="test">count(cda:versionNumber)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] versionNumber (CONF:1098-32753).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1967')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]"
                 priority="30"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1979']">
            <schxslt:rule pattern="d206e1979">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1979">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5382">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHOULD contain zero or more [0..*] telecom (CONF:1198-5382).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:languageCommunication) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5406">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:languageCommunication) &gt; 0]</xsl:attribute>
                     <svrl:text>This patient SHOULD contain zero or more [0..*] languageCommunication (CONF:1198-5406).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16787">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] code (CONF:1198-16787).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested-here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5430-c">
                     <xsl:attribute name="test">not(tested-here)</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] assignedPerson (CONF:1198-5430).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested-here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16783-c">
                     <xsl:attribute name="test">not(tested-here)</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] assignedAuthoringDevice (CONF:1198-16783).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author/cda:assignedAuthor[cda:assignedPerson]) = count(cda:author/cda:assignedAuthor[cda:assignedPerson and cda:id/@root='2.16.840.1.113883.4.6']))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32882-c">
                     <xsl:attribute name="test">count(cda:author/cda:assignedAuthor[cda:assignedPerson]) = count(cda:author/cda:assignedAuthor[cda:assignedPerson and cda:id/@root='2.16.840.1.113883.4.6'])</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] id (CONF:1198-32882) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-32884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:legalAuthenticator)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5579">
                     <xsl:attribute name="test">count(cda:legalAuthenticator)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] legalAuthenticator (CONF:1198-5579).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:performer) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14839">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:performer) &gt; 0]</xsl:attribute>
                     <svrl:text>This serviceEvent SHOULD contain zero or more [0..*] performer (CONF:1198-14839).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5375">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-5375).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 8)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5300-c">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 8</xsl:attribute>
                     <svrl:text>*SHOULD* be precise to day (CONF:1198-5300).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:maritalStatusCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5303">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:maritalStatusCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHOULD contain zero or one [0..1] maritalStatusCode, which SHALL be selected from ValueSet Marital Status urn:oid:2.16.840.1.113883.1.11.12212 DYNAMIC (CONF:1198-5303).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5326">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHOULD contain zero or one [0..1] code, which SHALL be selected from ValueSet Personal And Legal Relationship Role Type urn:oid:2.16.840.1.113883.11.20.12.1 DYNAMIC (CONF:1198-5326).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count( cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5359-c">
                     <xsl:attribute name="test">count( cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr)</xsl:attribute>
                     <svrl:text>The guardian, if present, SHOULD contain zero or more [0..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5359).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7993">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>The telecom, if present, SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7993).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[count(cda:country)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5404">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[count(cda:country)=1]</xsl:attribute>
                     <svrl:text>This addr SHOULD contain zero or one [0..1] country, which SHALL be selected from ValueSet Country urn:oid:2.16.840.1.113883.3.88.12.80.63 DYNAMIC (CONF:1198-5404).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[cda:country='US' or cda:country='USA'][count(cda:state)!=1])=0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5402-c">
                     <xsl:attribute name="test">count(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[cda:country='US' or cda:country='USA'][count(cda:state)!=1])=0</xsl:attribute>
                     <svrl:text>If country is US, this addr *SHALL* contain exactly one [[]1..1[]] state, which *SHALL* be selected from ValueSet StateValueSet 2.16.840.1.113883.3.88.12.80.1 *DYNAMIC* (CONF:1198-5402).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:proficiencyLevelCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9965">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:proficiencyLevelCode)=1]</xsl:attribute>
                     <svrl:text>The languageCommunication, if present, SHOULD contain zero or one [0..1] proficiencyLevelCode, which SHALL be selected from ValueSet LanguageAbilityProficiency urn:oid:2.16.840.1.113883.1.11.12199 DYNAMIC (CONF:1198-9965).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:preferenceInd)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5414">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:preferenceInd)=1]</xsl:attribute>
                     <svrl:text>The languageCommunication, if present, SHOULD contain zero or one [0..1] preferenceInd (CONF:1198-5414).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16820">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-16820).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7994">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7994).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7995">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7995).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity/cda:id) or cda:dataEnterer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16821">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity/cda:id) or cda:dataEnterer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-16821).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity/cda:telecom) or cda:dataEnterer/cda:assignedEntity/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7996">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity/cda:telecom) or cda:dataEnterer/cda:assignedEntity/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7996).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(testable))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9946-c">
                     <xsl:attribute name="test">not(testable)</xsl:attribute>
                     <svrl:text>If assignedEntity/id is a provider then this id, *SHOULD* include zero or one [[]0..1[]] id where id/@root ="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-9946).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16822">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-16822).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7998">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>This telecom SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7998).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity/cda:telecom) or cda:legalAuthenticator/cda:assignedEntity/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7999">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity/cda:telecom) or cda:legalAuthenticator/cda:assignedEntity/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7999).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant[@typeCode='IND']) = count(cda:participant/cda:associatedEntity[@classCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017AUG_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.11.20.9.33']/voc:code/@value]))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-10007-c">
                     <xsl:attribute name="test">count(cda:participant[@typeCode='IND']) = count(cda:participant/cda:associatedEntity[@classCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017AUG_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.11.20.9.33']/voc:code/@value])</xsl:attribute>
                     <svrl:text>When participant/@typeCode is *IND*, associatedEntity/@classCode *SHOULD* be selected from ValueSet 2.16.840.1.113883.11.20.9.33 INDRoleclassCodes *STATIC 2011-09-30* (CONF:1198-10007).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode[@code and @code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.10267']/voc:code/@value])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32889">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode[@code and @code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.10267']/voc:code/@value]</xsl:attribute>
                     <svrl:text>The functionCode, if present, SHOULD contain zero or one [0..1] @code, which SHOULD be selected from ValueSet ParticipationFunction urn:oid:2.16.840.1.113883.1.11.10267 STATIC (CONF:1198-32889).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14847">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-14847).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14842">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHOULD contain zero or one [0..1] code, which SHOULD be selected from ValueSet Healthcare Provider Taxonomy (HIPAA) urn:oid:2.16.840.1.114222.4.11.1066 DYNAMIC (CONF:1198-14842).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:confidentialityCode[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.16926']/voc:code/@value])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5259-v">
                     <xsl:attribute name="test">count(cda:confidentialityCode[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.16926']/voc:code/@value])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] confidentialityCode, which SHOULD be selected from ValueSet HL7 BasicConfidentialityKind urn:oid:2.16.840.1.113883.1.11.16926 STATIC (CONF:1198-5259).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16788-v">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code]</xsl:attribute>
                     <svrl:text>The code, if present, SHALL contain exactly one [1..1] @code, which SHOULD be selected from ValueSet Healthcare Provider Taxonomy (HIPAA) urn:oid:2.16.840.1.114222.4.11.1066 DYNAMIC (CONF:1198-16788).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1979')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:id[@root='2.16.840.1.113883.4.6']"
                 priority="29"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1979']">
            <schxslt:rule pattern="d206e1979">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-32882-branch-32882-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:id[@root='2.16.840.1.113883.4.6']" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-32882-branch-32882-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1979">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-32882-branch-32882-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:author/cda:assignedAuthor/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(@extension)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32885-branch-32882">
                     <xsl:attribute name="test">@extension</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] @extension (CONF:1198-32885).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1979')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator"
                 priority="28"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e1979']">
            <schxslt:rule pattern="d206e1979">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-5607-branch-5607-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-5607-branch-5607-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e1979">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.22.1.1-2015-08-01-5607-branch-5607-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.22.1.1' and @extension='2015-08-01']]/cda:authenticator</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(not(cda:assignedEntity/cda:id) or cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16824-branch-5607">
                     <xsl:attribute name="test">not(cda:assignedEntity/cda:id) or cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier  (CONF:1198-16824).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:assignedEntity/cda:telecom) or cda:assignedEntity/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-8000-branch-5607">
                     <xsl:attribute name="test">not(cda:assignedEntity/cda:telecom) or cda:assignedEntity/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-8000).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e1979')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]"
                 priority="27"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2105']">
            <schxslt:rule pattern="d206e2105">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2105">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:guardian) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-32">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:guardian) &gt; 0]</xsl:attribute>
                     <svrl:text>This patient SHOULD contain zero or more [0..*] guardian (CONF:3315-32).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:component/cda:structuredBody[count(cda:component[count(cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']])=1])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-142">
                     <xsl:attribute name="test">cda:component/cda:structuredBody[count(cda:component[count(cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']])=1])=1]</xsl:attribute>
                     <svrl:text>This structuredBody SHOULD contain zero or one [0..1] component (CONF:3315-142) such that it SHALL contain exactly one [1..1] Reportability Response Subject Section (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.2.1:2017-04-01) (CONF:3315-144).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:component/cda:structuredBody[count(cda:component[count(cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']])=1])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-631">
                     <xsl:attribute name="test">cda:component/cda:structuredBody[count(cda:component[count(cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']])=1])=1]</xsl:attribute>
                     <svrl:text>This structuredBody SHOULD contain zero or one [0..1] component (CONF:3315-631) such that it SHALL contain exactly one [1..1] Reportability Response Summary Section (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.2.2:2017-04-01) (CONF:3315-632).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:code[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.17660']/voc:code/@value or @nullFlavor])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-53-v">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter/cda:location/cda:healthCareFacility[count(cda:code[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.17660']/voc:code/@value or @nullFlavor])=1]</xsl:attribute>
                     <svrl:text>This healthCareFacility SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet ServiceDeliveryLocationRoleType urn:oid:2.16.840.1.113883.1.11.17660 (CONF:3315-53).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:componentOf/cda:encompassingEncounter[count(cda:code[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.13955']/voc:code/@value or @nullFlavor])=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-55-v">
                     <xsl:attribute name="test">cda:componentOf/cda:encompassingEncounter[count(cda:code[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.13955']/voc:code/@value or @nullFlavor])=1]</xsl:attribute>
                     <svrl:text>This encompassingEncounter SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet ActEncounterCode urn:oid:2.16.840.1.113883.1.11.13955 (CONF:3315-55).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5382">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHOULD contain zero or more [0..*] telecom (CONF:1198-5382).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:languageCommunication) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5406">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:languageCommunication) &gt; 0]</xsl:attribute>
                     <svrl:text>This patient SHOULD contain zero or more [0..*] languageCommunication (CONF:1198-5406).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16787">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] code (CONF:1198-16787).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested-here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5430-c">
                     <xsl:attribute name="test">not(tested-here)</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] assignedPerson (CONF:1198-5430).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(tested-here))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16783-c">
                     <xsl:attribute name="test">not(tested-here)</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] assignedAuthoringDevice (CONF:1198-16783).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:author/cda:assignedAuthor[cda:assignedPerson]) = count(cda:author/cda:assignedAuthor[cda:assignedPerson and cda:id/@root='2.16.840.1.113883.4.6']))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32882-c">
                     <xsl:attribute name="test">count(cda:author/cda:assignedAuthor[cda:assignedPerson]) = count(cda:author/cda:assignedAuthor[cda:assignedPerson and cda:id/@root='2.16.840.1.113883.4.6'])</xsl:attribute>
                     <svrl:text>This assignedAuthor SHOULD contain zero or one [0..1] id (CONF:1198-32882) such that it SHALL contain exactly one [1..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-32884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:legalAuthenticator)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5579">
                     <xsl:attribute name="test">count(cda:legalAuthenticator)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] legalAuthenticator (CONF:1198-5579).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:performer) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14839">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent) or cda:documentationOf/cda:serviceEvent[count(cda:performer) &gt; 0]</xsl:attribute>
                     <svrl:text>This serviceEvent SHOULD contain zero or more [0..*] performer (CONF:1198-14839).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5375">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-5375).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 8)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5300-c">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@nullFlavor or string-length(cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value) &gt;= 8</xsl:attribute>
                     <svrl:text>*SHOULD* be precise to day (CONF:1198-5300).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:recordTarget/cda:patientRole/cda:patient[count(cda:maritalStatusCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5303">
                     <xsl:attribute name="test">cda:recordTarget/cda:patientRole/cda:patient[count(cda:maritalStatusCode)=1]</xsl:attribute>
                     <svrl:text>This patient SHOULD contain zero or one [0..1] maritalStatusCode, which SHALL be selected from ValueSet Marital Status urn:oid:2.16.840.1.113883.1.11.12212 DYNAMIC (CONF:1198-5303).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5326">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>The guardian, if present, SHOULD contain zero or one [0..1] code, which SHALL be selected from ValueSet Personal And Legal Relationship Role Type urn:oid:2.16.840.1.113883.11.20.12.1 DYNAMIC (CONF:1198-5326).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count( cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5359-c">
                     <xsl:attribute name="test">count( cda:recordTarget/cda:patientRole/cda:patient/cda:guardian) &lt;= count(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:addr)</xsl:attribute>
                     <svrl:text>The guardian, if present, SHOULD contain zero or more [0..*] US Realm Address (AD.US.FIELDED) (identifier: urn:oid:2.16.840.1.113883.10.20.22.5.2) (CONF:1198-5359).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7993">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom) or cda:recordTarget/cda:patientRole/cda:patient/cda:guardian/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>The telecom, if present, SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7993).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[count(cda:country)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5404">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr) or cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[count(cda:country)=1]</xsl:attribute>
                     <svrl:text>This addr SHOULD contain zero or one [0..1] country, which SHALL be selected from ValueSet Country urn:oid:2.16.840.1.113883.3.88.12.80.63 DYNAMIC (CONF:1198-5404).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[cda:country='US' or cda:country='USA'][count(cda:state)!=1])=0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5402-c">
                     <xsl:attribute name="test">count(cda:recordTarget/cda:patientRole/cda:patient/cda:birthplace/cda:place/cda:addr[cda:country='US' or cda:country='USA'][count(cda:state)!=1])=0</xsl:attribute>
                     <svrl:text>If country is US, this addr *SHALL* contain exactly one [[]1..1[]] state, which *SHALL* be selected from ValueSet StateValueSet 2.16.840.1.113883.3.88.12.80.1 *DYNAMIC* (CONF:1198-5402).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:proficiencyLevelCode)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9965">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:proficiencyLevelCode)=1]</xsl:attribute>
                     <svrl:text>The languageCommunication, if present, SHOULD contain zero or one [0..1] proficiencyLevelCode, which SHALL be selected from ValueSet LanguageAbilityProficiency urn:oid:2.16.840.1.113883.1.11.12199 DYNAMIC (CONF:1198-9965).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:preferenceInd)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5414">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication) or cda:recordTarget/cda:patientRole/cda:patient/cda:languageCommunication[count(cda:preferenceInd)=1]</xsl:attribute>
                     <svrl:text>The languageCommunication, if present, SHOULD contain zero or one [0..1] preferenceInd (CONF:1198-5414).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16820">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-16820).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7994">
                     <xsl:attribute name="test">not(cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom) or cda:recordTarget/cda:patientRole/cda:providerOrganization/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7994).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:author/cda:assignedAuthor/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7995">
                     <xsl:attribute name="test">cda:author/cda:assignedAuthor/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7995).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity/cda:id) or cda:dataEnterer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16821">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity/cda:id) or cda:dataEnterer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-16821).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:dataEnterer/cda:assignedEntity/cda:telecom) or cda:dataEnterer/cda:assignedEntity/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7996">
                     <xsl:attribute name="test">not(cda:dataEnterer/cda:assignedEntity/cda:telecom) or cda:dataEnterer/cda:assignedEntity/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7996).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(testable))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-9946-c">
                     <xsl:attribute name="test">not(testable)</xsl:attribute>
                     <svrl:text>If assignedEntity/id is a provider then this id, *SHOULD* include zero or one [[]0..1[]] id where id/@root ="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-9946).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16822">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-16822).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7998">
                     <xsl:attribute name="test">cda:custodian/cda:assignedCustodian/cda:representedCustodianOrganization/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>This telecom SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7998).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:legalAuthenticator/cda:assignedEntity/cda:telecom) or cda:legalAuthenticator/cda:assignedEntity/cda:telecom[@use])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-7999">
                     <xsl:attribute name="test">not(cda:legalAuthenticator/cda:assignedEntity/cda:telecom) or cda:legalAuthenticator/cda:assignedEntity/cda:telecom[@use]</xsl:attribute>
                     <svrl:text>Such telecoms SHOULD contain zero or one [0..1] @use, which SHALL be selected from ValueSet Telecom Use (US Realm Header) urn:oid:2.16.840.1.113883.11.20.9.20 DYNAMIC (CONF:1198-7999).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant[@typeCode='IND']) = count(cda:participant/cda:associatedEntity[@classCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017AUG_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.11.20.9.33']/voc:code/@value]))">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-10007-c">
                     <xsl:attribute name="test">count(cda:participant[@typeCode='IND']) = count(cda:participant/cda:associatedEntity[@classCode=document('CDAR2_IG_PHCR_R2_RR_D1_2017AUG_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.11.20.9.33']/voc:code/@value])</xsl:attribute>
                     <svrl:text>When participant/@typeCode is *IND*, associatedEntity/@classCode *SHOULD* be selected from ValueSet 2.16.840.1.113883.11.20.9.33 INDRoleclassCodes *STATIC 2011-09-30* (CONF:1198-10007).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode[@code and @code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.10267']/voc:code/@value])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-32889">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:functionCode[@code and @code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.10267']/voc:code/@value]</xsl:attribute>
                     <svrl:text>The functionCode, if present, SHOULD contain zero or one [0..1] @code, which SHOULD be selected from ValueSet ParticipationFunction urn:oid:2.16.840.1.113883.1.11.10267 STATIC (CONF:1198-32889).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6'])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14847">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity/cda:id[@root='2.16.840.1.113883.4.6']</xsl:attribute>
                     <svrl:text>Such ids SHOULD contain zero or one [0..1] @root="2.16.840.1.113883.4.6" National Provider Identifier (CONF:1198-14847).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:code)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-14842">
                     <xsl:attribute name="test">not(cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity) or cda:documentationOf/cda:serviceEvent/cda:performer/cda:assignedEntity[count(cda:code)=1]</xsl:attribute>
                     <svrl:text>This assignedEntity SHOULD contain zero or one [0..1] code, which SHOULD be selected from ValueSet Healthcare Provider Taxonomy (HIPAA) urn:oid:2.16.840.1.114222.4.11.1066 DYNAMIC (CONF:1198-14842).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:confidentialityCode[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.16926']/voc:code/@value])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-5259-v">
                     <xsl:attribute name="test">count(cda:confidentialityCode[@code=document('CDAR2_IG_PHCR_R2_RR_D1_2017DEC_VOC.xml')/voc:systems/voc:system[@valueSetOid='2.16.840.1.113883.1.11.16926']/voc:code/@value])=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] confidentialityCode, which SHOULD be selected from ValueSet HL7 BasicConfidentialityKind urn:oid:2.16.840.1.113883.1.11.16926 STATIC (CONF:1198-5259).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1198-16788-v">
                     <xsl:attribute name="test">not(cda:author/cda:assignedAuthor/cda:code) or cda:author/cda:assignedAuthor/cda:code[@code]</xsl:attribute>
                     <svrl:text>The code, if present, SHALL contain exactly one [1..1] @code, which SHOULD be selected from ValueSet Healthcare Provider Taxonomy (HIPAA) urn:oid:2.16.840.1.114222.4.11.1066 DYNAMIC (CONF:1198-16788).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2105')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']"
                 priority="26"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2105']">
            <schxslt:rule pattern="d206e2105">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-83-branch-83-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-83-branch-83-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2105">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-83-branch-83-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='PRCP']</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(cda:intendedRecipient[count(cda:receivedOrganization)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-677-branch-83">
                     <xsl:attribute name="test">cda:intendedRecipient[count(cda:receivedOrganization)=1]</xsl:attribute>
                     <svrl:text>This intendedRecipient SHOULD contain zero or one [0..1] receivedOrganization (CONF:3315-677).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-688-branch-83">
                     <xsl:attribute name="test">not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHOULD contain zero or more [0..*] id (CONF:3315-688).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-690-branch-83">
                     <xsl:attribute name="test">not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHOULD contain zero or more [0..*] telecom (CONF:3315-690).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2105')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='TRC']"
                 priority="25"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2105']">
            <schxslt:rule pattern="d206e2105">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-678-branch-678-warnings for context "cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='TRC']" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-678-branch-678-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='TRC']</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2105">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.1.2-2017-04-01-678-branch-678-warnings">
                  <xsl:attribute name="context">cda:ClinicalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.1.2' and @extension='2017-04-01']]/cda:informationRecipient[@typeCode='TRC']</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(not(cda:intendedRecipient) or cda:intendedRecipient[count(cda:receivedOrganization)=1])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-682-branch-678">
                     <xsl:attribute name="test">not(cda:intendedRecipient) or cda:intendedRecipient[count(cda:receivedOrganization)=1]</xsl:attribute>
                     <svrl:text>This intendedRecipient SHOULD contain zero or one [0..1] receivedOrganization (CONF:3315-682).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-697-branch-678">
                     <xsl:attribute name="test">not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHOULD contain zero or more [0..*] id (CONF:3315-697).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-699-branch-678">
                     <xsl:attribute name="test">not(cda:intendedRecipient/cda:receivedOrganization) or cda:intendedRecipient/cda:receivedOrganization[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>The receivedOrganization, if present, SHOULD contain zero or more [0..*] telecom (CONF:3315-699).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2105')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]"
                 priority="24"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2257']">
            <schxslt:rule pattern="d206e2257">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-warnings for context "cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2257">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.1-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2257')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]"
                 priority="23"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2265']">
            <schxslt:rule pattern="d206e2265">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-warnings for context "cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2265">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.2-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2265')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]"
                 priority="22"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2273']">
            <schxslt:rule pattern="d206e2273">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-warnings for context "cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2273">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.2.3-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:section[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.2.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2273')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]"
                 priority="21"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2281']">
            <schxslt:rule pattern="d206e2281">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-warnings for context "cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2281">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.34-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.34' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2281')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]"
                 priority="20"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2289']">
            <schxslt:rule pattern="d206e2289">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2289">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.7-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.7' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-16884-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet Patient Education urn:oid:2.16.840.1.113883.11.20.9.34 DYNAMIC (CONF:1098-16884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2289')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]"
                 priority="19"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2303']">
            <schxslt:rule pattern="d206e2303">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2303">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.8-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.8' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-16884-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet Patient Education urn:oid:2.16.840.1.113883.11.20.9.34 DYNAMIC (CONF:1098-16884).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2303')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]"
                 priority="18"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2316']">
            <schxslt:rule pattern="d206e2316">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2316">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.9-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.9' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:text[@xsi:type='ST'])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-431">
                     <xsl:attribute name="test">count(cda:text[@xsi:type='ST'])=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] text (CONF:3315-431).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2316')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]"
                 priority="17"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2325']">
            <schxslt:rule pattern="d206e2325">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-warnings for context "cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2325">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.10-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.10' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:setId)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32752">
                     <xsl:attribute name="test">count(cda:setId)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] setId (CONF:1098-32752).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:versionNumber)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-1098-32753">
                     <xsl:attribute name="test">count(cda:versionNumber)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] versionNumber (CONF:1098-32753).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2325')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]"
                 priority="16"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2341']">
            <schxslt:rule pattern="d206e2341">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2341">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.12-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.12' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(cda:value[@xsi:type='CD'][@code])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-732">
                     <xsl:attribute name="test">cda:value[@xsi:type='CD'][@code]</xsl:attribute>
                     <svrl:text>This value SHOULD contain zero or one [0..1] @code (CONF:3315-732).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:value[@xsi:type='CD'][@codeSystem])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-733">
                     <xsl:attribute name="test">cda:value[@xsi:type='CD'][@codeSystem]</xsl:attribute>
                     <svrl:text>This value SHOULD contain zero or one [0..1] @codeSystem (CONF:3315-733).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:value[@xsi:type='CD'][@displayName])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-734">
                     <xsl:attribute name="test">cda:value[@xsi:type='CD'][@displayName]</xsl:attribute>
                     <svrl:text>This value SHOULD contain zero or one [0..1] @displayName (CONF:3315-734).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2341')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]"
                 priority="15"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2356']">
            <schxslt:rule pattern="d206e2356">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-warnings for context "cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2356">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.13-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:organizer[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.13' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:component[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']])=1])=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-326">
                     <xsl:attribute name="test">count(cda:component[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']])=1])=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] component (CONF:3315-326) such that it SHALL contain exactly one [1..1] Reporting Timeframe (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.14:2017-04-01) (CONF:3315-330).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:component[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']])=1]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-328">
                     <xsl:attribute name="test">count(cda:component[count(cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']])=1]) &gt; 0</xsl:attribute>
                     <svrl:text>SHOULD contain zero or more [0..*] component (CONF:3315-328) such that it SHALL contain exactly one [1..1] External Resources (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.20:2017-04-01) (CONF:3315-453).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-338">
                     <xsl:attribute name="test">count(cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]) &gt; 0</xsl:attribute>
                     <svrl:text>SHOULD contain zero or more [0..*] Responsible Agency (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.4.2:2017-04-01) (CONF:3315-338).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2356')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]"
                 priority="14"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2371']">
            <schxslt:rule pattern="d206e2371">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2371">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.14-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.14' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-250-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-250).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:value[@xsi:type='PQ'][@unit])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-672-v">
                     <xsl:attribute name="test">cda:value[@xsi:type='PQ'][@unit]</xsl:attribute>
                     <svrl:text>This value SHALL contain exactly one [1..1] @unit, which SHOULD be selected from CodeSystem UCUM (urn:oid:2.16.840.1.113883.6.8) DYNAMIC (CONF:3315-672).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2371')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]"
                 priority="13"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2384']">
            <schxslt:rule pattern="d206e2384">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-warnings for context "cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2384">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.17-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:externalDocument[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.17' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:text)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-273">
                     <xsl:attribute name="test">count(cda:text)=1</xsl:attribute>
                     <svrl:text>SHOULD contain zero or one [0..1] text (CONF:3315-273).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2384')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]"
                 priority="12"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2393']">
            <schxslt:rule pattern="d206e2393">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2393">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.19-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.19' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:entryRelationship[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']])=1]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-533">
                     <xsl:attribute name="test">count(cda:entryRelationship[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']])=1]) &gt; 0</xsl:attribute>
                     <svrl:text>SHOULD contain zero or more [0..*] entryRelationship (CONF:3315-533) such that it SHALL contain exactly one [1..1] Determination of Reportability Reason (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.26:2017-04-01) (CONF:3315-536).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:entryRelationship[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']])=1]) &gt; 0)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-534">
                     <xsl:attribute name="test">count(cda:entryRelationship[count(cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']])=1]) &gt; 0</xsl:attribute>
                     <svrl:text>SHOULD contain zero or more [0..*] entryRelationship (CONF:3315-534) such that it SHALL contain exactly one [1..1] Determination of Reportability Rule (identifier: urn:hl7ii:2.16.840.1.113883.10.20.15.2.3.27:2017-04-01) (CONF:3315-538).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-348-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-348).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2393')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]"
                 priority="11"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2408']">
            <schxslt:rule pattern="d206e2408">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-warnings for context "cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2408">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.1-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.1' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(cda:participantRole[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-394">
                     <xsl:attribute name="test">cda:participantRole[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHOULD contain zero or more [0..*] id (CONF:3315-394).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:addr) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-397">
                     <xsl:attribute name="test">cda:participantRole[count(cda:addr) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHOULD contain at least one [1..*] addr (CONF:3315-397).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
               <xsl:if test="not(cda:participantRole[count(cda:telecom) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-398">
                     <xsl:attribute name="test">cda:participantRole[count(cda:telecom) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHOULD contain at least one [1..*] telecom (CONF:3315-398).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2408')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]"
                 priority="10"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2423']">
            <schxslt:rule pattern="d206e2423">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-warnings for context "cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2423">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.2-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.2' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(cda:participantRole[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-412">
                     <xsl:attribute name="test">cda:participantRole[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHOULD contain zero or more [0..*] id (CONF:3315-412).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2423')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]"
                 priority="9"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2432']">
            <schxslt:rule pattern="d206e2432">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-warnings for context "cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2432">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.4.3-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:participant[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.4.3' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(cda:participantRole[count(cda:id) &gt; 0])">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-425">
                     <xsl:attribute name="test">cda:participantRole[count(cda:id) &gt; 0]</xsl:attribute>
                     <svrl:text>This participantRole SHOULD contain zero or more [0..*] id (CONF:3315-425).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2432')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]"
                 priority="8"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2441']">
            <schxslt:rule pattern="d206e2441">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2441">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.20-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.20' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2441')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]"
                 priority="7"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2450']">
            <schxslt:rule pattern="d206e2450">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2450">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.22-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.22' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2450')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]"
                 priority="6"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2458']">
            <schxslt:rule pattern="d206e2458">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2458">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.21-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.21' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-469-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-469).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2458')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]"
                 priority="5"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2467']">
            <schxslt:rule pattern="d206e2467">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2467">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.26-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.26' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-515-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-515).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2467')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]"
                 priority="4"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2476']">
            <schxslt:rule pattern="d206e2476">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2476">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.27-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.27' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-525-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code (CONF:3315-525).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2476')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]"
                 priority="3"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2485']">
            <schxslt:rule pattern="d206e2485">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-warnings for context "cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2485">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.29-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.29' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2485')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]"
                 priority="2"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2493']">
            <schxslt:rule pattern="d206e2493">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2493">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.30-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.30' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2493')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]"
                 priority="1"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2502']">
            <schxslt:rule pattern="d206e2502">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2502">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.32-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.32' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(count(cda:code)=1)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}"
                                      id="a-3315-659-v">
                     <xsl:attribute name="test">count(cda:code)=1</xsl:attribute>
                     <svrl:text>SHALL contain exactly one [1..1] code, which SHOULD be selected from ValueSet eICR Processing Status Reason Detail Type urn:oid:2.16.840.1.113883.10.20.15.2.3.32 DYNAMIC (CONF:3315-659).</svrl:text>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2502')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:template match="cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]"
                 priority="0"
                 mode="d206e161">
      <xsl:param name="schxslt:patterns-matched" as="xs:string*"/>
      <xsl:choose>
         <xsl:when test="$schxslt:patterns-matched[. = 'd206e2511']">
            <schxslt:rule pattern="d206e2511">
               <xsl:comment xmlns:svrl="http://purl.oclc.org/dsdl/svrl">WARNING: Rule r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-warnings for context "cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]" shadowed by preceding rule</xsl:comment>
               <svrl:suppressed-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                     id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:suppressed-rule>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="$schxslt:patterns-matched"/>
            </xsl:next-match>
         </xsl:when>
         <xsl:otherwise>
            <schxslt:rule pattern="d206e2511">
               <svrl:fired-rule xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                id="r-urn-hl7ii-2.16.840.1.113883.10.20.15.2.3.33-2017-04-01-warnings">
                  <xsl:attribute name="context">cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.15.2.3.33' and @extension='2017-04-01']]</xsl:attribute>
               </svrl:fired-rule>
               <xsl:if test="not(.)">
                  <svrl:failed-assert xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                                      location="{schxslt:location(.)}">
                     <xsl:attribute name="test">.</xsl:attribute>
                  </svrl:failed-assert>
               </xsl:if>
            </schxslt:rule>
            <xsl:next-match>
               <xsl:with-param name="schxslt:patterns-matched"
                               as="xs:string*"
                               select="($schxslt:patterns-matched, 'd206e2511')"/>
            </xsl:next-match>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:template>
   <xsl:function name="schxslt:location" as="xs:string">
      <xsl:param name="node" as="node()"/>
      <xsl:variable name="segments" as="xs:string*">
         <xsl:for-each select="($node/ancestor-or-self::node())">
            <xsl:variable name="position">
               <xsl:number level="single"/>
            </xsl:variable>
            <xsl:choose>
               <xsl:when test=". instance of element()">
                  <xsl:value-of select="concat('Q{', namespace-uri(.), '}', local-name(.), '[', $position, ']')"/>
               </xsl:when>
               <xsl:when test=". instance of attribute()">
                  <xsl:value-of select="concat('@Q{', namespace-uri(.), '}', local-name(.))"/>
               </xsl:when>
               <xsl:when test=". instance of processing-instruction()">
                  <xsl:value-of select="concat('processing-instruction(&#34;', name(.), '&#34;)[', $position, ']')"/>
               </xsl:when>
               <xsl:when test=". instance of comment()">
                  <xsl:value-of select="concat('comment()[', $position, ']')"/>
               </xsl:when>
               <xsl:when test=". instance of text()">
                  <xsl:value-of select="concat('text()[', $position, ']')"/>
               </xsl:when>
               <xsl:otherwise/>
            </xsl:choose>
         </xsl:for-each>
      </xsl:variable>
      <xsl:value-of select="concat('/', string-join($segments, '/'))"/>
   </xsl:function>
</xsl:transform>
