<!--
    HL7 CDA to Accessible HTML Transformation Stylesheet
    Project: DIBBs eCR Refiner
    Author: Skylight / CDC / Lantana Group conventions
    Purpose: Transform CDA XML (eICR, RR) into semantically rich, accessible HTML for browser display.
    See: xslt-plan.md for roadmap, field mapping, and best practices.
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:cda="urn:hl7-org:v3"
    exclude-result-prefixes="cda">

    <!-- Output HTML5 -->
    <xsl:output method="html" indent="yes" encoding="UTF-8"/>

    <!-- Root template: match CDA ClinicalDocument root -->
    <xsl:template match="/cda:ClinicalDocument">
        <html lang="en">
            <head>
                <meta charset="UTF-8"/>
                <title>CDA Report</title>
                <style type="text/css">
                    body { font-family: 'Segoe UI', Arial, sans-serif; background: #fff; color: #222; }
                    h1, h2 { font-weight: bold; margin-top: 1em; }
                    table { border-collapse: collapse; width: 100%; margin: 1em 0; }
                    th, td { border: 1px solid #ddd; padding: 0.5em; text-align: left; }
                    th { background: #f6f6f6; font-weight: bold; }
                    tr:nth-child(even) { background: #f9f9f9; }
                    ul { list-style: disc inside; margin: 0.5em 0 0.5em 1em; }
                    a { color: #0645ad; text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>CDA Report</h1>
                <!-- Patient, Provider, eICR ID, Narrative Sections will be rendered here by further templates -->
                <xsl:call-template name="render-patient-info"/>
                <xsl:call-template name="render-provider-info"/>
                <xsl:call-template name="render-eicr-id"/>
                <xsl:call-template name="render-narrative"/>
            </body>
        </html>
    </xsl:template>

    <!-- Placeholder named templates -->
    <xsl:template name="render-patient-info">
        <!-- Patient Information Table -->
        <h2>Patient Information</h2>
        <table>
            <tr>
                <th>Name</th>
                <td>
                    <xsl:variable name="given" select="cda:recordTarget/cda:patientRole/cda:patient/cda:name/cda:given"/>
                    <xsl:variable name="family" select="cda:recordTarget/cda:patientRole/cda:patient/cda:name/cda:family"/>
                    <xsl:value-of select="$given"/> <xsl:value-of select="$family"/>
                </td>
            </tr>
            <tr>
                <th>Patient ID</th>
                <td>
                    <xsl:for-each select="cda:recordTarget/cda:patientRole/cda:id">
                        <xsl:value-of select="@root"/>
                        <xsl:if test="@extension"> - <xsl:value-of select="@extension"/></xsl:if>
                        <xsl:if test="position()!=last()">, </xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
            <tr>
                <th>Date of Birth</th>
                <td>
                    <xsl:value-of select="cda:recordTarget/cda:patientRole/cda:patient/cda:birthTime/@value"/>
                </td>
            </tr>
            <tr>
                <th>Sex</th>
                <td>
                    <xsl:value-of select="cda:recordTarget/cda:patientRole/cda:patient/cda:administrativeGenderCode/@displayName"/>
                </td>
            </tr>
            <tr>
                <th>Race</th>
                <td>
                    <xsl:value-of select="cda:recordTarget/cda:patientRole/cda:patient/cda:raceCode/@displayName"/>
                </td>
            </tr>
            <tr>
                <th>Ethnicity</th>
                <td>
                    <xsl:value-of select="cda:recordTarget/cda:patientRole/cda:patient/cda:ethnicGroupCode/@displayName"/>
                </td>
            </tr>
            <tr>
                <th>Address</th>
                <td>
                    <xsl:for-each select="cda:recordTarget/cda:patientRole/cda:addr">
                        <xsl:value-of select="cda:streetAddressLine"/>, <xsl:value-of select="cda:city"/>, <xsl:value-of select="cda:state"/> <xsl:value-of select="cda:postalCode"/>, <xsl:value-of select="cda:country"/>
                        <xsl:if test="position()!=last()"><br/></xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
            <tr>
                <th>Contact</th>
                <td>
                    <xsl:for-each select="cda:recordTarget/cda:patientRole/cda:telecom">
                        <xsl:value-of select="@value"/>
                        <xsl:if test="position()!=last()">, </xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
        </table>
    </xsl:template>
    <xsl:template name="render-provider-info">
        <!-- Provider/Recipient Information Table -->
        <h2>Primary Information Recipient</h2>
        <table>
            <tr>
                <th>Name</th>
                <td>
                    <xsl:variable name="prefix" select="cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name/cda:prefix"/>
                    <xsl:variable name="given" select="cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name/cda:given"/>
                    <xsl:variable name="family" select="cda:informationRecipient/cda:intendedRecipient/cda:informationRecipient/cda:name/cda:family"/>
                    <xsl:value-of select="$prefix"/> <xsl:value-of select="$given"/> <xsl:value-of select="$family"/>
                </td>
            </tr>
            <tr>
                <th>ID</th>
                <td>
                    <xsl:for-each select="cda:informationRecipient/cda:intendedRecipient/cda:id">
                        <xsl:value-of select="@root"/>
                        <xsl:if test="@extension"> - <xsl:value-of select="@extension"/></xsl:if>
                        <xsl:if test="position()!=last()">, </xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
            <tr>
                <th>Address</th>
                <td>
                    <xsl:for-each select="cda:informationRecipient/cda:intendedRecipient/cda:addr">
                        <xsl:value-of select="cda:streetAddressLine"/>, <xsl:value-of select="cda:city"/>, <xsl:value-of select="cda:state"/> <xsl:value-of select="cda:postalCode"/>, <xsl:value-of select="cda:country"/>
                        <xsl:if test="position()!=last()"><br/></xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
            <tr>
                <th>Contact</th>
                <td>
                    <xsl:for-each select="cda:informationRecipient/cda:intendedRecipient/cda:telecom">
                        <xsl:value-of select="@value"/>
                        <xsl:if test="position()!=last()">, </xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
        </table>
    </xsl:template>
    <xsl:template name="render-eicr-id">
        <!-- eICR Identifier Table -->
        <h2>eICR Identifier</h2>
        <table>
            <tr>
                <th>eICR ID</th>
                <td>
                    <xsl:for-each select="cda:component/cda:structuredBody/cda:section/cda:entry/cda:act/cda:reference/cda:externalDocument/cda:id">
                        <xsl:choose>
                            <xsl:when test="@extension">
                                <xsl:value-of select="@extension"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="@root"/>
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:if test="position()!=last()">, </xsl:if>
                    </xsl:for-each>
                </td>
            </tr>
        </table>
    </xsl:template>
    <xsl:template name="render-narrative">
        <!-- Narrative Content Section -->
        <h2>Narrative Summary</h2>
        <xsl:for-each select="cda:component/cda:structuredBody/cda:section/cda:text/cda:paragraph">
            <p>
                <xsl:value-of select="."/>
            </p>
        </xsl:for-each>
        <!-- Resources and Links -->
        <xsl:for-each select="cda:component/cda:structuredBody/cda:section/cda:text/cda:content/cda:linkHtml">
            <ul>
                <li>
                    <a href="{@href}"><xsl:value-of select="."/></a>
                </li>
            </ul>
        </xsl:for-each>
    </xsl:template>

    <!-- Additional templates and comments for extensibility will be added as implementation proceeds -->
</xsl:stylesheet>
