<?xml version="1.0" encoding="UTF-8"?>
<!--
  Title: Lantana's CDA Stylesheet
  Original Filename: cda.xsl
  Usage: This stylesheet is designed for use with clinical documents

  Revision History: 2015-08-31 Eric Parapini - Original Commit
  Revision History: 2015-08-31 Eric Parapini - Updating Built in CSS for Camara conversion, fixed the rendering issue with Table of contents linking (Sean's help)
  Revision History: 2015-09-01 Eric Parapini - Updating Colors, Revamping the CSS, New Vision of the Header Information, Hover Tables, Formatted Patient Information Initial Release
  Revision History: 2015-09-03 Eric Parapini - Cleaned up CSS - Documentationof, added Header/Body/Footer Elements
  Revision History: 2015-10-01 Eric Parapini - CSS is now separated, Encounter of is moved down, including Bootstrap elements
  Revision History: 2015-10-02 Eric Parapini - CSS now has new styles that will take over the other spots
  Revision History: 2015-10-05 Eric Parapini - CSS updated, better use of bootstrap elements, responsive
  Revision History: 2015-10-06 Eric Parapini - Stylesheet rendering updated, Author section redone, tables now render in section elements
  Revision History: 2015-10-07 Eric Parapini - Changed the font sizes
  Revision History: 2015-10-21 Eric Parapini - Fixed logic, cleaned everything up, making the document more consistent
  Revision History: 2015-10-22 Eric Parapini - Converted some more sections to the modern bootstrap formatting, reorganized the footer
                                               Fixed up the assigned entity formatting
                                               Fixed up the informant
  Revision History: 2015-10-22 Eric Parapini - Fixed a few more things, disabled table of content generation for now
                                               Removed the timezone offset in date renderings, deemed unecessary.
  Revision History: 2015-12-10 Eric Parapini - Removed some of the additional time errors
  Revision History: 2016-02-22 Eric Parapini - Added Logo space, added in some javascript background support for interactive navigation bars
  Revision History: 2016-02-23 Eric Parapini - Added smooth scrolling, making the document easier to navigate
  Revision History: 2016-02-24 Eric Parapini - Added some CSS and content to make the table of contents styling easier to control
  Revision History: 2016-02-29 Eric Parapini - Added patient information entry in the table of contents
  Revision History: 2016-03-09 Eric Parapini - Adding in simple matches for common identifier OIDS (SSN, Driver's licenses)
                                               Additional fixes to the TOC, working on scrollspy working
                                               Fixed issue with Care = PROV not being recrognized
  Revision History: 2016-05-10 Eric Parapini - Updated Table of Contents to properly highlight location within document
  Revision History: 2016-05-17 Eric Parapini - Updated location of the next of kin to be with the patient information
  Revision History: 2016-06-08 Eric Parapini - Removed Emergency Contact Table of Contents
  Revision History: 2016-08-06 Eric Parapini - Table of Contents Drag and Drop
  Revision History: 2016-08-08 Eric Parapini - Document Type shows up in rendered view
  Revision History: 2016-11-14 Eric Parapini - Further Separating supporting libraries
  Revision History: 2017-02-09 Eric Parapini - Fixed Bug removing styleCodes
  Revision History: 2017-02-24 Eric Parapini - Fixed titles
  Revision History: 2017-02-26 Eric Parapini - Cleaned up some code
  Revision History: 2017-03-31 Eric Parapini - Whitespace issues fixing
  Revision History: 2017-04-05 Eric Parapini - Whitespace tweaking in the header, added patient ID highlighting
  Revision History: 2017-04-06 Eric Parapini - Tweaked encounter whitespace organization

  Revision History: 2019-04-20 Sarah Gaunt   - Added author time rendering
  Revision History: 2019-04-20 Sarah Gaunt   - Added parent/guardian rendering
  Revision History: 2019-04-21 Sarah Gaunt   - Updated serviceEvent rendering to properly render if @classCode missing (i.e. uses default @classCode)
  Revision History: 2020-01-13 Sarah Gaunt   - Updated author rendering to to include all information
  Revision History: 2020-01-13 Sarah Gaunt   - Updated rendering to deal with External Encounter (missing most encompassingEncounter information) more gracefully
  Revision History: 2020-05-11 Sarah Gaunt   - Updated telecom rendering (fixed typo) and updated contact handling

  Revision History: 2020-09-26 Sarah Gaunt   - eCR Requirements: Stylesheets (September 2020 Updates)
                                              #1 | Change the eICR and RR stylesheets so demographics will display on the HTMLs when no ID’s are present in Patient Role
                                              #2 | Correct issue with eICR stylesheet in rendering health care facility location
  Revision History: 2020-10-05 Sarah Gaunt    - Tweaked the above change to the health care facility location rendering - now uses display name of code plus "of"
                                                ServiceProviderLocation/name
  Revision History: 2021-05-10 Sarah Gaunt    - Added: sdtc:deceasedDate, sdtc:raceCode, sdtc:ethnicGroupCode
  Revision History: 2021-10-19 Sarah Gaunt    - Added preferred language display
  Revision History: 2021-10-20 Sarah Gaunt    - Added processing for patient addr useable period
  Revision History: 2021-12-02 Sarah Gaunt    - Remove legacy SVN version and author information after migration from HL7 GForge SVN to HL7 Github
  Revision History: 2023-05-18 Sarah Gaunt    - Update to not display SSN if it is present
  Revision History: 2025-05-21 Sarah Gaunt    - Update to translate 3 character language codes

  This style sheet is based on a major revision of the original CDA XSL, which was made possible thanks to the contributions of:
  - Jingdong Li
  - KH
  - Rick Geimer
  - Sean McIlvenna
  - Dale Nelson

-->
<!--
Copyright 2016-2021+ Lantana Consulting Group

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
<xsl:stylesheet xmlns:sdtc="urn:hl7-org:sdtc" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
    <!-- This is where all the styles are loaded -->

    <xsl:output xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" method="html" indent="yes" version="4.01" encoding="UTF-8" doctype-system="http://www.w3.org/TR/html4/strict.dtd"
        doctype-public="-//W3C//DTD HTML 4.01//EN" />
    <xsl:param xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="limit-external-images" select="'yes'" />
    <!-- A vertical bar separated list of URI prefixes, such as "http://www.example.com|https://www.example.com" -->
    <xsl:param xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="external-image-whitelist" />
    <xsl:param xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="logo-location" />
    <!-- string processing variables -->
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="lc" select="'abcdefghijklmnopqrstuvwxyz'" />
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="uc" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'" />
    <!-- removes the following characters, in addition to line breaks "':;?`{}“”„‚’ -->
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="simple-sanitizer-match">
        <xsl:text>
&#13;"':;?`{}“”„‚’</xsl:text>
    </xsl:variable>
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="simple-sanitizer-replace" select="'***************'" />
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="javascript-injection-warning">WARNING: Javascript injection attempt detected in source CDA document.
        Terminating</xsl:variable>
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="malicious-content-warning">WARNING: Potentially malicious content found in CDA document.</xsl:variable>

    <!-- global variable title -->
    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="title">
        <xsl:choose>
            <xsl:when test="string-length(/n1:ClinicalDocument/n1:title) &gt;= 1">
                <xsl:value-of select="/n1:ClinicalDocument/n1:title" />
            </xsl:when>
            <xsl:when test="/n1:ClinicalDocument/n1:code/@displayName">
                <xsl:value-of select="/n1:ClinicalDocument/n1:code/@displayName" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>Clinical Document</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>


    <!-- Main -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="/">
        <xsl:apply-templates select="n1:ClinicalDocument" />
    </xsl:template>

    <!-- produce browser rendered, human readable clinical document -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:ClinicalDocument">
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <xsl:comment> Do NOT edit this HTML directly: it was generated via an XSLT transformation from a CDA Release 2 XML document. </xsl:comment>
                <title class="cda-title">
                    <xsl:value-of select="$title" />
                </title>
                <xsl:call-template name="jquery" />
                <xsl:call-template name="jquery-ui" />
                <xsl:call-template name="bootstrap-css" />
                <xsl:call-template name="bootstrap-javascript" />
                <xsl:call-template name="lantana-js" />
                <xsl:call-template name="lantana-css" />
            </head>
            <body data-spy="scroll" data-target="#navbar-cda">

                <div class="cda-render toc col-md-3" role="complementary">

                    <!-- produce table of contents -->
                    <xsl:if test="not(//n1:nonXMLBody)">
                        <xsl:if test="count(/n1:ClinicalDocument/n1:component/n1:structuredBody/n1:component[n1:section]) &gt; 0">
                            <xsl:call-template name="make-tableofcontents" />
                        </xsl:if>
                    </xsl:if>
                </div>

                <!-- Container: CDA Render -->
                <div class="cda-render container-fluid col-md-9 cda-render-main" role="main">

                    <row>
                        <h1 id="top" class="cda-title">
                            <xsl:value-of select="$title" />
                        </h1>
                    </row>
                    <!-- START display top portion of clinical document -->
                    <div class="top container-fluid">
                        <xsl:call-template name="recordTarget" />
                        <xsl:call-template name="documentationOf" />
                        <xsl:call-template name="author" />
                        <xsl:call-template name="componentOf" />
                        <xsl:call-template name="participant" />
                        <xsl:call-template name="informant" />
                        <xsl:call-template name="informationRecipient" />
                        <xsl:call-template name="legalAuthenticator" />
                    </div>
                    <!-- END display top portion of clinical document -->

                    <!-- produce human readable document content -->
                    <div class="middle" id="doc-clinical-info">
                        <xsl:apply-templates select="n1:component/n1:structuredBody | n1:component/n1:nonXMLBody" />
                    </div>
                    <!-- Footer -->
                    <div class="bottom" id="doc-info">
                        <xsl:call-template name="authenticator" />
                        <xsl:call-template name="custodian" />
                        <xsl:call-template name="dataEnterer" />
                        <xsl:call-template name="documentGeneral" />
                    </div>
                </div>

            </body>
        </html>



        <!-- BEGIN TEMPLATES -->
    </xsl:template>
    <!-- generate table of contents -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="make-tableofcontents">

        <nav class="cda-render hidden-print hidden-xs hidden-sm affix toc-box" id="navbar-cda">
            <div class="container-fluid cda-render toc-header-container">
                <xsl:if test="$logo-location">
                    <div class="col-md-1">
                        <img src="logo.png" class="img-responsive" alt="Logo">
                            <xsl:attribute name="src">
                                <xsl:value-of select="$logo-location" />
                            </xsl:attribute>
                        </img>
                    </div>
                </xsl:if>
                <div class="cda-render toc-header">
                    <xsl:for-each select="/n1:ClinicalDocument/n1:recordTarget/n1:patientRole">
                        <xsl:call-template name="show-name">
                            <xsl:with-param name="name" select="n1:patient/n1:name" />
                        </xsl:call-template>
                    </xsl:for-each>
                </div>
                <div class="cda-render toc-header">
                    <xsl:value-of select="$title" />
                </div>
            </div>
            <ul class="cda-render nav nav-stacked fixed" id="navbar-list-cda">
                <li>
                    <a class="cda-render lantana-toc" href="#top">BACK TO TOP</a>
                </li>
                <li>
                    <a class="cda-render lantana-toc" href="#cda-patient">DEMOGRAPHICS</a>
                </li>
                <li>
                    <a class="cda-render lantana-toc" href="#author-performer">AUTHORING DETAILS</a>
                </li>
                <li>
                    <a class="cda-render lantana-toc bold" href="#doc-clinical-info">Clinical Sections</a>
                    <ul class="cda-render nav nav-stacked fixed" id="navbar-list-cda-sortable">
                        <xsl:for-each select="n1:component/n1:structuredBody/n1:component/n1:section/n1:title">
                            <li>
                                <a class="cda-render lantana-toc" href="#{generate-id(.)}">
                                    <xsl:value-of select="." />
                                </a>
                            </li>
                        </xsl:for-each>
                    </ul>
                </li>
                <li>
                    <a class="cda-render lantana-toc" href="#doc-info">SIGNATURES</a>
                </li>
            </ul>
        </nav>
    </xsl:template>
    <!-- header elements -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="documentGeneral">
        <div class="container-fluid">
            <h2 class="section-title col-md-6">
                <xsl:text>Document Information</xsl:text>
            </h2>
            <div class="table-responsive col-md-6">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>
                                <xsl:text>Document Identifier</xsl:text>
                            </th>
                            <th>
                                <xsl:text>Document Created</xsl:text>
                            </th>
                        </tr>

                    </thead>
                    <tbody>
                        <tr>
                            <td>
                                <xsl:call-template name="show-id">
                                    <xsl:with-param name="id" select="n1:id" />
                                </xsl:call-template>
                            </td>
                            <td>
                                <xsl:call-template name="show-time">
                                    <xsl:with-param name="datetime" select="n1:effectiveTime" />
                                </xsl:call-template>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </xsl:template>
    <!-- confidentiality -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="confidentiality">
        <table class="header_table">
            <tbody>
                <td class="td_header_role_name">
                    <xsl:text>Confidentiality</xsl:text>
                </td>
                <td class="td_header_role_value">
                    <xsl:choose>
                        <xsl:when test="n1:confidentialityCode/@code = 'N'">
                            <xsl:text>Normal</xsl:text>
                        </xsl:when>
                        <xsl:when test="n1:confidentialityCode/@code = 'R'">
                            <xsl:text>Restricted</xsl:text>
                        </xsl:when>
                        <xsl:when test="n1:confidentialityCode/@code = 'V'">
                            <xsl:text>Very restricted</xsl:text>
                        </xsl:when>
                    </xsl:choose>
                    <xsl:if test="n1:confidentialityCode/n1:originalText">
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="n1:confidentialityCode/n1:originalText" />
                    </xsl:if>
                </td>
            </tbody>
        </table>
    </xsl:template>
    <!-- author -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="author">
        <xsl:if test="n1:author">
            <div class="header container-fluid">
                <!-- SG: removed assignedAuthor from for-each to grab time, then added back in inside loop -->
                <xsl:for-each select="n1:author">
                    <!-- Author -->
                    <div class="container-fluid">
                        <!-- Author Name-->
                        <div class="col-md-6">
                            <h2 class="section-title col-md-6" id="author-performer">
                                <xsl:text>Author</xsl:text>
                            </h2>
                            <div class="header-group-content col-md-8">
                                <!-- SG: Added time -->
                                <xsl:if test="n1:time">
                                    <div class="row">
                                        <div class="attribute-title col-md-6">
                                            <xsl:text>Time: </xsl:text>
                                        </div>
                                        <div class="col-md-6">
                                            <xsl:call-template name="show-time">
                                                <xsl:with-param name="datetime" select="n1:time" />
                                            </xsl:call-template>
                                        </div>
                                    </div>
                                </xsl:if>
                                <xsl:choose>
                                    <xsl:when test="n1:assignedAuthor/n1:assignedPerson/n1:name">
                                        <div class="row">
                                            <div class="col-md-8">
                                                <xsl:call-template name="show-name">
                                                    <xsl:with-param name="name" select="n1:assignedAuthor/n1:assignedPerson/n1:name" />
                                                </xsl:call-template>
                                                <!-- Getting this down further for the Author Organization section -->
                                                <!--<xsl:if test="n1:assignedAuthor/n1:representedOrganization">
                          <xsl:text> - </xsl:text>
                          <xsl:call-template name="show-name">
                            <xsl:with-param name="name" select="n1:assignedAuthor/n1:representedOrganization/n1:name" />
                          </xsl:call-template>
                        </xsl:if>-->
                                            </div>
                                        </div>
                                    </xsl:when>
                                    <xsl:when test="n1:assignedAuthor/n1:assignedAuthoringDevice/n1:softwareName">
                                        <div class="row">
                                            <div class="col-md-8">
                                                <xsl:call-template name="show-code">
                                                    <xsl:with-param name="code" select="n1:assignedAuthor/n1:assignedAuthoringDevice/n1:softwareName" />
                                                </xsl:call-template>
                                                <!-- Getting this down further for the Author Organization section -->
                                                <!--<xsl:if test="n1:assignedAuthor/n1:representedOrganization">
                          <xsl:text> - </xsl:text>
                          <xsl:call-template name="show-name">
                            <xsl:with-param name="name" select="n1:assignedAuthor/n1:representedOrganization/n1:name" />
                          </xsl:call-template>
                        </xsl:if>-->
                                            </div>
                                        </div>
                                    </xsl:when>
                                </xsl:choose>
                                <xsl:if test="n1:assignedAuthor/n1:id">
                                    <div class="row">
                                        <div class="col-md-8">
                                            <xsl:for-each select="n1:assignedAuthor/n1:id">
                                                <xsl:call-template name="show-id">
                                                    <xsl:with-param name="id" select="." />
                                                </xsl:call-template>
                                            </xsl:for-each>
                                        </div>
                                    </div>
                                </xsl:if>
                                <!--<xsl:choose>
                  <xsl:when test="n1:assignedAuthor/n1:representedOrganization">
                    <div class="row">
                      <div class="col-md-8">
                        <xsl:call-template name="show-name">
                          <xsl:with-param name="name" select="n1:assignedAuthor/n1:representedOrganization/n1:name" />
                        </xsl:call-template>
                      </div>
                    </div>
                  </xsl:when>
                  <xsl:otherwise>
                    <div class="row">
                      <div class="col-md-8">
                        <xsl:for-each select="n1:assignedAuthor/n1:id">
                          <xsl:call-template name="show-id">
                            <xsl:with-param name="id" select="." />
                          </xsl:call-template>
                        </xsl:for-each>
                      </div>
                    </div>
                  </xsl:otherwise>
                </xsl:choose>-->
                            </div>
                        </div>
                        <!-- Author Contact -->
                        <div class="col-md-6">
                            <xsl:if test="n1:assignedAuthor/n1:addr | n1:assignedAuthor/n1:telecom">
                                <h2 class="section-title col-md-6">Contact</h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:call-template name="show-contactInfo">
                                        <xsl:with-param name="contact" select="n1:assignedAuthor" />
                                    </xsl:call-template>
                                </div>
                            </xsl:if>
                        </div>
                    </div>
                    <!-- ********************** -->

                    <xsl:if test="n1:assignedAuthor/n1:representedOrganization">
                        <div class="container-fluid">
                            <div class="col-md-6">
                                <h2 class="section-title col-md-6" id="author-performer">
                                    <xsl:text>Author Organization</xsl:text>
                                </h2>
                                <div class="header-group-content col-md-8">

                                    <xsl:for-each select="n1:assignedAuthor/n1:representedOrganization/n1:name">
                                        <div class="row">
                                            <div class="col-md-8">
                                                <xsl:call-template name="show-name">
                                                    <xsl:with-param name="name" select="." />
                                                </xsl:call-template>
                                            </div>
                                        </div>
                                    </xsl:for-each>

                                    <xsl:for-each select="n1:assignedAuthor/n1:representedOrganization/n1:id">
                                        <div class="row">
                                            <div class="col-md-8">
                                                <xsl:for-each select=".">
                                                    <xsl:call-template name="show-id">
                                                        <xsl:with-param name="id" select="." />
                                                    </xsl:call-template>
                                                </xsl:for-each>
                                            </div>
                                        </div>
                                    </xsl:for-each>

                                </div>
                            </div>
                            <div class="col-md-6">
                                <xsl:if test="n1:assignedAuthor/n1:representedOrganization/n1:addr | n1:assignedAuthor/n1:representedOrganization/n1:telecom">
                                    <h2 class="section-title col-md-6">Contact</h2>
                                    <div class="header-group-content col-md-8">
                                        <xsl:call-template name="show-contactInfo">
                                            <xsl:with-param name="contact" select="n1:assignedAuthor/n1:representedOrganization" />
                                        </xsl:call-template>
                                    </div>
                                </xsl:if>
                            </div>
                        </div>
                    </xsl:if>
                    <!-- ********************** -->
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <!--  authenticator -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="authenticator">
        <xsl:if test="n1:authenticator">
            <div class="header container-fluid">
                <xsl:for-each select="n1:authenticator">
                    <div class="col-md-6">
                        <h2 class="section-title col-md-6">
                            <xsl:text>Signed</xsl:text>
                        </h2>
                        <div class="header-group-content col-md-8">
                            <xsl:call-template name="show-name">
                                <xsl:with-param name="name" select="n1:assignedEntity/n1:assignedPerson/n1:name" />
                            </xsl:call-template>
                            <xsl:text> at </xsl:text>
                            <xsl:call-template name="show-time">
                                <xsl:with-param name="datetime" select="n1:time" />
                            </xsl:call-template>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <xsl:if test="n1:assignedEntity/n1:addr | n1:assignedEntity/n1:telecom">
                            <h2 class="section-title col-md-6">
                                <xsl:text>Contact</xsl:text>
                            </h2>
                            <div class="header-group-content col-md-8">
                                <xsl:call-template name="show-contactInfo">
                                    <xsl:with-param name="contact" select="n1:assignedEntity" />
                                </xsl:call-template>
                            </div>
                        </xsl:if>
                    </div>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <!-- legalAuthenticator -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="legalAuthenticator">
        <div class="container-fluid">
            <xsl:if test="n1:legalAuthenticator">
                <div class="header container-fluid">
                    <div class="col-md-6">
                        <h2 class="section-title col-md-6">
                            <xsl:text>Legal authenticator</xsl:text>
                        </h2>
                        <div class="header-group-content col-md-8">
                            <xsl:call-template name="show-assignedEntity">
                                <xsl:with-param name="asgnEntity" select="n1:legalAuthenticator/n1:assignedEntity" />
                            </xsl:call-template>
                            <xsl:text> </xsl:text>
                            <xsl:call-template name="show-sig">
                                <xsl:with-param name="sig" select="n1:legalAuthenticator/n1:signatureCode" />
                            </xsl:call-template>
                            <xsl:if test="n1:legalAuthenticator/n1:time/@value">
                                <xsl:text> at </xsl:text>
                                <xsl:call-template name="show-time">
                                    <xsl:with-param name="datetime" select="n1:legalAuthenticator/n1:time" />
                                </xsl:call-template>
                            </xsl:if>
                        </div>
                    </div>
                    <xsl:if test="n1:legalAuthenticator/n1:assignedEntity/n1:addr | n1:legalAuthenticator/n1:assignedEntity/n1:telecom">
                        <div class="col-md-6">
                            <h2 class="col-md-6 section-title">Contact</h2>
                            <div class="header-group-content col-md-8">
                                <xsl:call-template name="show-contactInfo">
                                    <xsl:with-param name="contact" select="n1:legalAuthenticator/n1:assignedEntity" />
                                </xsl:call-template>
                            </div>
                        </div>
                    </xsl:if>
                </div>
            </xsl:if>
        </div>
    </xsl:template>
    <!-- dataEnterer -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="dataEnterer">
        <xsl:if test="n1:dataEnterer">
            <div class="container-fluid header">
                <div class="col-md-6">
                    <h2 class="section-title col-md-6">
                        <xsl:text>Entered by</xsl:text>
                    </h2>
                    <div class="col-md-6 header-group-content">
                        <xsl:call-template name="show-assignedEntity">
                            <xsl:with-param name="asgnEntity" select="n1:dataEnterer/n1:assignedEntity" />
                        </xsl:call-template>
                    </div>
                </div>
                <div class="col-md-6">
                    <xsl:if test="n1:dataEnterer/n1:assignedEntity/n1:addr | n1:dataEnterer/n1:assignedEntity/n1:telecom">
                        <h2 class="section-title col-md-6">
                            <xsl:text>Contact</xsl:text>
                        </h2>
                        <div class="col-md-6 header-group-content">
                            <xsl:call-template name="show-contactInfo">
                                <xsl:with-param name="contact" select="n1:dataEnterer/n1:assignedEntity" />
                            </xsl:call-template>
                        </div>
                    </xsl:if>
                </div>
            </div>
        </xsl:if>
    </xsl:template>
    <!-- componentOf -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="componentOf">
        <xsl:if test="n1:componentOf">
            <div class="header container-fluid">
                <xsl:for-each select="n1:componentOf/n1:encompassingEncounter">
                    <div class="container-fluid col-md-8">
                        <div class="container-fluid">
                            <h2 class="section-title col-md-10">
                                <xsl:text>Encounter</xsl:text>
                            </h2>
                            <div class="header-group-content col-md-10">
                                <xsl:if test="n1:id[not(@nullFlavor)]">
                                    <div class="row">
                                        <div class="attribute-title col-md-2">
                                            <xsl:text>Identifier</xsl:text>
                                        </div>
                                        <div class="col-md-6">
                                            <xsl:call-template name="show-id">
                                                <xsl:with-param name="id" select="n1:id" />
                                            </xsl:call-template>
                                        </div>
                                    </div>
                                </xsl:if>
                                <xsl:if test="n1:code">
                                    <div class="row">
                                        <div class="attribute-title col-md-2">
                                            <xsl:text>Type</xsl:text>
                                        </div>
                                        <div class="col-md-6">
                                            <xsl:call-template name="show-code">
                                                <xsl:with-param name="code" select="n1:code" />
                                            </xsl:call-template>
                                        </div>
                                    </div>
                                </xsl:if>
                                <xsl:if test="n1:effectiveTime[not(@nullFlavor)] and not(n1:effectiveTime/n1:low/@nullFlavor)">

                                    <div class="row">
                                        <div class="attribute-title col-md-2">
                                            <xsl:text>Date</xsl:text>
                                        </div>

                                        <xsl:choose>
                                            <xsl:when test="n1:effectiveTime/@value">
                                                <div class="col-md-4">
                                                    <xsl:call-template name="show-time">
                                                        <xsl:with-param name="datetime" select="n1:effectiveTime" />
                                                    </xsl:call-template>
                                                </div>
                                            </xsl:when>
                                            <xsl:when test="n1:effectiveTime/n1:low">
                                                <div class="col-md-4">
                                                    <span class="attribute-title">
                                                        <xsl:text>From: </xsl:text>
                                                    </span>
                                                    <xsl:call-template name="show-time">
                                                        <xsl:with-param name="datetime" select="n1:effectiveTime/n1:low" />
                                                    </xsl:call-template>
                                                </div>
                                                <xsl:if test="n1:effectiveTime/n1:high">
                                                    <div class="col-md-4">
                                                        <span class="attribute-title">
                                                            <xsl:text>To: </xsl:text>
                                                        </span>
                                                        <xsl:call-template name="show-time">
                                                            <xsl:with-param name="datetime" select="n1:effectiveTime/n1:high" />
                                                        </xsl:call-template>
                                                    </div>
                                                </xsl:if>
                                            </xsl:when>
                                        </xsl:choose>

                                    </div>
                                </xsl:if>
                                <xsl:if
                                    test="n1:location/n1:healthCareFacility and not(n1:location/n1:healthCareFacility/n1:code/@nullFlavor) and not(n1:location/n1:healthCareFacility/n1:location/n1:addr/n1:state/@nullFlavor) and not(n1:location/n1:healthCareFacility/n1:location/n1:serviceProviderOrganization/n1:addr/n1:state/@nullFlavor)">
                                    <div class="row">
                                        <div class="attribute-title col-md-2">
                                            <xsl:text>Location</xsl:text>
                                        </div>
                                        <div class="col-md-6">
                                            <xsl:choose>
                                                <xsl:when test="n1:location/n1:healthCareFacility/n1:location/n1:name">
                                                    <xsl:call-template name="show-name">
                                                        <xsl:with-param name="name" select="n1:location/n1:healthCareFacility/n1:location/n1:name" />
                                                    </xsl:call-template>
                                                    <xsl:for-each select="n1:location/n1:healthCareFacility/n1:serviceProviderOrganization/n1:name">
                                                        <xsl:text> of </xsl:text>
                                                        <xsl:call-template name="show-name">
                                                            <xsl:with-param name="name" select="." />
                                                        </xsl:call-template>
                                                    </xsl:for-each>
                                                </xsl:when>
                                                <xsl:when test="n1:location/n1:healthCareFacility/n1:code">
                                                    <xsl:call-template name="show-code">
                                                        <xsl:with-param name="code" select="n1:location/n1:healthCareFacility/n1:code" />
                                                    </xsl:call-template>
                                                    <xsl:for-each select="n1:location/n1:healthCareFacility/n1:serviceProviderOrganization/n1:name">
                                                        <xsl:text> of </xsl:text>
                                                        <xsl:call-template name="show-name">
                                                            <xsl:with-param name="name" select="." />
                                                        </xsl:call-template>
                                                    </xsl:for-each>
                                                </xsl:when>
                                                <xsl:otherwise>
                                                    <xsl:if test="n1:location/n1:healthCareFacility/n1:id">
                                                        <span class="attribute-title">
                                                            <xsl:text>ID: </xsl:text>
                                                        </span>
                                                        <xsl:for-each select="n1:location/n1:healthCareFacility/n1:id">
                                                            <xsl:call-template name="show-id">
                                                                <xsl:with-param name="id" select="." />
                                                            </xsl:call-template>
                                                        </xsl:for-each>
                                                    </xsl:if>
                                                </xsl:otherwise>
                                            </xsl:choose>
                                        </div>
                                    </div>
                                </xsl:if>
                            </div>
                            <xsl:if
                                test="n1:responsibleParty and not(n1:responsibleParty/n1:assignedEntity/n1:id/@nullFlavor) and not(n1:responsibleParty/n1:assignedEntity/n1:addr/n1:state/@nullFlavor) and not(n1:responsibleParty/n1:assignedEntity/n1:assignedPerson/n1:name/n1:given/@nullFlavor) and not(n1:responsibleParty/n1:assignedEntity/n1:representedOrganization/n1:addr/n1:state/@nullFlavor)">
                                <div class="col-md-6">
                                    <h2 class="section-title col-md-6">
                                        <xsl:text>Responsible Party</xsl:text>
                                    </h2>
                                    <div class="header-group-content col-md-8">
                                        <xsl:call-template name="show-assignedEntity">
                                            <xsl:with-param name="asgnEntity" select="n1:responsibleParty/n1:assignedEntity" />
                                        </xsl:call-template>
                                    </div>
                                </div>
                            </xsl:if>
                            <xsl:if
                                test="(n1:responsibleParty/n1:assignedEntity/n1:addr and not(n1:responsibleParty/n1:assignedEntity/n1:addr/n1:state/@nullFlavor)) or (n1:responsibleParty/n1:assignedEntity/n1:telecom and not(n1:responsibleParty/n1:assignedEntity/n1:telecom/@nullFlavor))">
                                <div class="col-md-6">
                                    <h2 class="section-title col-md-6">
                                        <xsl:text>Contact</xsl:text>
                                    </h2>
                                    <div class="header-group-content col-md-8">
                                        <xsl:call-template name="show-contactInfo">
                                            <xsl:with-param name="contact" select="n1:responsibleParty/n1:assignedEntity" />
                                        </xsl:call-template>
                                    </div>
                                </div>
                            </xsl:if>
                        </div>
                    </div>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <!-- custodian -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="custodian">
        <xsl:if test="n1:custodian">
            <div class="container-fluid header">
                <div class="col-md-6">
                    <h2 class="section-title col-md-6">
                        <xsl:text>Document maintained by</xsl:text>
                    </h2>
                    <div class="header-group-content col-md-8">
                        <xsl:choose>
                            <xsl:when test="n1:custodian/n1:assignedCustodian/n1:representedCustodianOrganization/n1:name">
                                <xsl:call-template name="show-name">
                                    <xsl:with-param name="name" select="n1:custodian/n1:assignedCustodian/n1:representedCustodianOrganization/n1:name" />
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:for-each select="n1:custodian/n1:assignedCustodian/n1:representedCustodianOrganization/n1:id">
                                    <xsl:call-template name="show-id" />
                                    <xsl:if test="position() != last()"> </xsl:if>
                                </xsl:for-each>
                            </xsl:otherwise>
                        </xsl:choose>
                    </div>
                </div>
                <xsl:if test="n1:custodian/n1:assignedCustodian/n1:representedCustodianOrganization/n1:addr | n1:custodian/n1:assignedCustodian/n1:representedCustodianOrganization/n1:telecom">
                    <div class="col-md-6">
                        <h2 class="section-title col-md-6"> Contact </h2>
                        <div class="header-group-content col-md-8">
                            <xsl:call-template name="show-contactInfo">
                                <xsl:with-param name="contact" select="n1:custodian/n1:assignedCustodian/n1:representedCustodianOrganization" />
                            </xsl:call-template>
                        </div>
                    </div>
                </xsl:if>
            </div>
        </xsl:if>
    </xsl:template>
    <!-- documentationOf -->
    <!-- SG: Updated to show section information even if the @classCode isn't present (i.e. default value) -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="documentationOf">
        <xsl:if test="n1:documentationOf">
            <div class="header container-fluid">
                <xsl:for-each select="n1:documentationOf">
                    <xsl:choose>
                        <!-- SG: Updated - this was testing for both @classCode AND serviceEvent/code previously -->
                        <xsl:when test="n1:serviceEvent/n1:code">
                            <!-- SG: serviceEvent/@classCode defaults to "ACT" so if it's not there,
                   we need to use default value, otherwise the whole serviceEvent section is blank,
                   even if it contains data-->
                            <xsl:variable name="vServiceEventClassCode">
                                <xsl:choose>
                                    <xsl:when test="n1:serviceEvent/@classCode">
                                        <xsl:value-of select="n1:serviceEvent/@classCode" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="'ACT'" />
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:variable>
                            <div class="container-fluid">
                                <div class="container-fluid">
                                    <xsl:variable name="displayName">
                                        <xsl:call-template name="show-actClassCode">
                                            <xsl:with-param name="clsCode" select="$vServiceEventClassCode" />
                                        </xsl:call-template>
                                    </xsl:variable>
                                    <xsl:if test="$displayName">
                                        <div class="col-md-6">
                                            <h2 class="section-title">
                                                <xsl:call-template name="firstCharCaseUp">
                                                    <xsl:with-param name="data" select="$displayName" />
                                                </xsl:call-template>
                                            </h2>
                                        </div>
                                        <div class="header-group-content col-md-8">
                                            <xsl:call-template name="show-code">
                                                <xsl:with-param name="code" select="n1:serviceEvent/n1:code" />
                                            </xsl:call-template>
                                            <xsl:if test="n1:serviceEvent/n1:effectiveTime">
                                                <xsl:choose>
                                                    <xsl:when test="n1:serviceEvent/n1:effectiveTime/@value">
                                                        <xsl:text> at </xsl:text>
                                                        <xsl:call-template name="show-time">
                                                            <xsl:with-param name="datetime" select="n1:serviceEvent/n1:effectiveTime" />
                                                        </xsl:call-template>
                                                    </xsl:when>
                                                    <xsl:when test="n1:serviceEvent/n1:effectiveTime/n1:low">
                                                        <xsl:text> from </xsl:text>
                                                        <xsl:call-template name="show-time">
                                                            <xsl:with-param name="datetime" select="n1:serviceEvent/n1:effectiveTime/n1:low" />
                                                        </xsl:call-template>
                                                        <xsl:if test="n1:serviceEvent/n1:effectiveTime/n1:high">
                                                            <xsl:text> to </xsl:text>
                                                            <xsl:call-template name="show-time">
                                                                <xsl:with-param name="datetime" select="n1:serviceEvent/n1:effectiveTime/n1:high" />
                                                            </xsl:call-template>
                                                        </xsl:if>
                                                    </xsl:when>
                                                </xsl:choose>
                                            </xsl:if>
                                        </div>
                                    </xsl:if>
                                </div>
                            </div>
                        </xsl:when>
                    </xsl:choose>
                    <xsl:for-each select="n1:serviceEvent/n1:performer">
                        <div class="header-group container-fluid">
                            <xsl:variable name="displayName">
                                <xsl:call-template name="show-participationType">
                                    <xsl:with-param name="ptype" select="@typeCode" />
                                </xsl:call-template>
                                <xsl:if test="n1:functionCode/@code">
                                    <xsl:text> </xsl:text>
                                    <xsl:call-template name="show-participationFunction">
                                        <xsl:with-param name="pFunction" select="n1:functionCode/@code" />
                                    </xsl:call-template>
                                </xsl:if>
                            </xsl:variable>
                            <div class="container-fluid">
                                <h2 class="section-title col-md-6" id="service-event">
                                    <xsl:text>Service Event</xsl:text>
                                </h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:call-template name="show-assignedEntity">
                                        <xsl:with-param name="asgnEntity" select="n1:assignedEntity" />
                                    </xsl:call-template>
                                </div>
                                <div class="header-group-content col-md-8">
                                    <xsl:if test="../n1:effectiveTime/n1:low">
                                        <xsl:call-template name="show-time">
                                            <xsl:with-param name="datetime" select="../n1:effectiveTime/n1:low" />
                                        </xsl:call-template>
                                    </xsl:if>

                                    <xsl:if test="../n1:effectiveTime/n1:high"> - <xsl:call-template name="show-time">
                                            <xsl:with-param name="datetime" select="../n1:effectiveTime/n1:high" />
                                        </xsl:call-template>
                                    </xsl:if>
                                </div>
                            </div>
                        </div>
                    </xsl:for-each>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <!-- inFulfillmentOf -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="inFulfillmentOf">
        <xsl:if test="n1:infulfillmentOf">
            <xsl:for-each select="n1:inFulfillmentOf">
                <xsl:text>In fulfillment of</xsl:text>
                <xsl:for-each select="n1:order">
                    <xsl:for-each select="n1:id">
                        <xsl:call-template name="show-id" />
                    </xsl:for-each>
                    <xsl:for-each select="n1:code">
                        <xsl:text> </xsl:text>
                        <xsl:call-template name="show-code">
                            <xsl:with-param name="code" select="." />
                        </xsl:call-template>
                    </xsl:for-each>
                    <xsl:for-each select="n1:priorityCode">
                        <xsl:text> </xsl:text>
                        <xsl:call-template name="show-code">
                            <xsl:with-param name="code" select="." />
                        </xsl:call-template>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:if>
    </xsl:template>
    <!-- informant -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="informant">
        <xsl:if test="n1:informant">
            <div class="header container-fluid">
                <xsl:for-each select="n1:informant">
                    <div class="container-fluid">
                        <div class="col-md-6">
                            <h2 class="section-title col-md-6">
                                <xsl:text>Informant</xsl:text>
                            </h2>
                            <div class="header-group-content col-md-8">
                                <xsl:if test="n1:assignedEntity">
                                    <xsl:call-template name="show-assignedEntity">
                                        <xsl:with-param name="asgnEntity" select="n1:assignedEntity" />
                                    </xsl:call-template>
                                </xsl:if>
                                <xsl:if test="n1:relatedEntity">
                                    <xsl:call-template name="show-relatedEntity">
                                        <xsl:with-param name="relatedEntity" select="n1:relatedEntity" />
                                    </xsl:call-template>
                                </xsl:if>
                            </div>
                        </div>
                        <xsl:choose>
                            <xsl:when test="n1:assignedEntity/n1:addr | n1:assignedEntity/n1:telecom">
                                <div class="col-md-6">
                                    <h2 class="section-title col-md-6">
                                        <xsl:text>Contact</xsl:text>
                                    </h2>
                                    <div class="header-group-content col-md-8">
                                        <xsl:if test="n1:assignedEntity">
                                            <xsl:call-template name="show-contactInfo">
                                                <xsl:with-param name="contact" select="n1:assignedEntity" />
                                            </xsl:call-template>
                                        </xsl:if>
                                    </div>
                                </div>
                            </xsl:when>
                            <xsl:when test="n1:relatedEntity/n1:addr | n1:relatedEntity/n1:telecom">
                                <div class="col-md-6">
                                    <h2 class="col-md-6 section-title">
                                        <xsl:text>Contact</xsl:text>
                                    </h2>
                                    <div class="col-md-6 header-group-content">
                                        <xsl:if test="n1:relatedEntity">
                                            <xsl:call-template name="show-contactInfo">
                                                <xsl:with-param name="contact" select="n1:relatedEntity" />
                                            </xsl:call-template>
                                        </xsl:if>
                                    </div>
                                </div>
                            </xsl:when>
                        </xsl:choose>
                    </div>
                </xsl:for-each>
            </div>
        </xsl:if>
    </xsl:template>
    <!-- informantionRecipient -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="informationRecipient">
        <div class="container-fluid">
            <xsl:if test="n1:informationRecipient">
                <div class="container-fluid header">
                    <xsl:for-each select="n1:informationRecipient">
                        <div class="container-fluid">
                            <h2 class="section-title col-md-6">
                                <xsl:text>Information Recipient</xsl:text>
                            </h2>
                            <div class="col-md-6 header-group-content">
                                <xsl:choose>
                                    <xsl:when test="n1:intendedRecipient/n1:informationRecipient/n1:name">
                                        <xsl:for-each select="n1:intendedRecipient/n1:informationRecipient">
                                            <xsl:call-template name="show-name">
                                                <xsl:with-param name="name" select="n1:name" />
                                            </xsl:call-template>
                                            <xsl:if test="position() != last()"> </xsl:if>
                                        </xsl:for-each>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:for-each select="n1:intendedRecipient">
                                            <xsl:for-each select="n1:id">
                                                <xsl:call-template name="show-id" />
                                            </xsl:for-each>
                                            <xsl:if test="position() != last()"> </xsl:if>
                                        </xsl:for-each>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </div>
                            <div class="col-md-6">
                                <xsl:if test="n1:intendedRecipient/n1:addr | n1:intendedRecipient/n1:telecom">
                                    <h2 class="section-title col-md-6">
                                        <xsl:text>Contact</xsl:text>
                                    </h2>
                                    <div class="col-md-6">
                                        <xsl:call-template name="show-contactInfo">
                                            <xsl:with-param name="contact" select="n1:intendedRecipient" />
                                        </xsl:call-template>
                                    </div>
                                </xsl:if>
                            </div>
                        </div>
                    </xsl:for-each>
                </div>
            </xsl:if>
        </div>
    </xsl:template>
    <!-- participant -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="participant">
        <div class="container-fluid">
            <xsl:if test="n1:participant">
                <div class="header container-fluid">
                    <xsl:for-each select="n1:participant">
                        <xsl:if test="not(n1:associatedEntity/@classCode = 'ECON' or n1:associatedEntity/@classCode = 'NOK')">
                            <xsl:variable name="participtRole">
                                <xsl:call-template name="translateRoleAssoCode">
                                    <xsl:with-param name="classCode" select="n1:associatedEntity/@classCode" />
                                    <xsl:with-param name="code" select="n1:associatedEntity/n1:code" />
                                </xsl:call-template>
                            </xsl:variable>
                            <div class="col-md-6">
                                <h2 class="col-md-6 section-title">
                                    <xsl:choose>
                                        <xsl:when test="$participtRole">
                                            <xsl:call-template name="firstCharCaseUp">
                                                <xsl:with-param name="data" select="$participtRole" />
                                            </xsl:call-template>
                                        </xsl:when>
                                        <xsl:otherwise>
                                            <xsl:text>Participant</xsl:text>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:if test="n1:functionCode">
                                        <xsl:call-template name="show-code">
                                            <xsl:with-param name="code" select="n1:functionCode" />
                                        </xsl:call-template>
                                    </xsl:if>
                                    <xsl:call-template name="show-associatedEntity">
                                        <xsl:with-param name="assoEntity" select="n1:associatedEntity" />
                                    </xsl:call-template>
                                    <xsl:if test="n1:time">
                                        <xsl:if test="n1:time/n1:low">
                                            <xsl:text> from </xsl:text>
                                            <xsl:call-template name="show-time">
                                                <xsl:with-param name="datetime" select="n1:time/n1:low" />
                                            </xsl:call-template>
                                        </xsl:if>
                                        <xsl:if test="n1:time/n1:high">
                                            <xsl:text> to </xsl:text>
                                            <xsl:call-template name="show-time">
                                                <xsl:with-param name="datetime" select="n1:time/n1:high" />
                                            </xsl:call-template>
                                        </xsl:if>
                                    </xsl:if>
                                    <xsl:if test="position() != last()">
                                        <br />
                                    </xsl:if>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <xsl:if test="n1:associatedEntity/n1:addr | n1:associatedEntity/n1:telecom">
                                    <h2 class="section-title col-md-6">
                                        <xsl:text>Contact</xsl:text>
                                    </h2>
                                    <div class="col-md-6 header-group-content">
                                        <xsl:call-template name="show-contactInfo">
                                            <xsl:with-param name="contact" select="n1:associatedEntity" />
                                        </xsl:call-template>
                                    </div>
                                </xsl:if>
                            </div>
                        </xsl:if>
                    </xsl:for-each>
                </div>
            </xsl:if>
        </div>
    </xsl:template>

    <!-- recordTarget / Patient -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="recordTarget">
        <div class="header container-fluid" id="cda-patient">
            <xsl:for-each select="/n1:ClinicalDocument/n1:recordTarget/n1:patientRole">
                <!-- SG: Removed the if as no patient demos were showing up when id was nullFlavor -->
                <!--        <xsl:if test="not(n1:id/@nullFlavor)">-->
                <div class="patient-heading container-fluid">
                    <div class="patient-name row">
                        <xsl:call-template name="show-name">
                            <xsl:with-param name="name" select="n1:patient/n1:name" />
                        </xsl:call-template>
                    </div>
                    <div class="patient-identifier container-fluid">
                        <div class="attribute-title row">Patient Identifiers</div>
                        <xsl:choose>
                            <xsl:when test="not(n1:id) or (n1:id/@nullFlavor and not(n1:id/@extension))">No id provided</xsl:when>
                        </xsl:choose>
                        <!-- SG: Don't display id if it's an SSN -->
                        <xsl:for-each select="n1:id[not(@root='2.16.840.1.113883.4.1')]">
                            <div class="row">
                                <div class="col-md-6 patient-id">
                                    <xsl:call-template name="show-id" />
                                </div>
                            </div>
                        </xsl:for-each>
                    </div>
                </div>
                <div class="patient-info container-fluid">
                    <div class="col-md-6">
                        <h2 class="section-title col-md-6">About</h2>
                        <div class="header-group-content col-md-8">
                            <div class="row">
                                <div class="attribute-title col-md-6">
                                    <xsl:text>Date of Birth</xsl:text>
                                </div>
                                <div class="col-md-6">
                                    <xsl:call-template name="show-time">
                                        <xsl:with-param name="datetime" select="n1:patient/n1:birthTime" />
                                    </xsl:call-template>
                                </div>
                            </div>
                            <!-- SG: 20210510 Added deceased display -->
                            <xsl:if test="n1:patient/sdtc:deceasedInd/@value = 'true'">

                                <div class="row">
                                    <div class="attribute-title col-md-6">
                                        <xsl:text>Deceased Date</xsl:text>
                                    </div>
                                    <div class="col-md-6">
                                        <xsl:call-template name="show-time">
                                            <xsl:with-param name="datetime" select="n1:patient/sdtc:deceasedTime" />
                                        </xsl:call-template>
                                    </div>
                                </div>
                            </xsl:if>
                            <div class="row">
                                <div class="attribute-title col-md-6">
                                    <xsl:text>Sex</xsl:text>
                                </div>
                                <div class="col-md-6">
                                    <xsl:for-each select="n1:patient/n1:administrativeGenderCode">
                                        <xsl:call-template name="show-gender" />
                                    </xsl:for-each>
                                </div>
                            </div>
                            <xsl:if test="n1:patient/n1:raceCode | (n1:patient/n1:ethnicGroupCode)">
                                <div class="row">
                                    <div class="attribute-title col-md-6">
                                        <xsl:text>Race</xsl:text>
                                    </div>
                                    <div class="col-md-6">
                                        <xsl:choose>
                                            <xsl:when test="n1:patient/n1:raceCode">
                                                <xsl:for-each select="n1:patient/n1:raceCode">
                                                    <xsl:call-template name="show-race-ethnicity" />
                                                    <!-- SG: 20210510 Added extra raceCode-->
                                                </xsl:for-each>
                                                <xsl:for-each select="n1:patient/sdtc:raceCode">
                                                    <xsl:text>, </xsl:text>
                                                    <xsl:call-template name="show-race-ethnicity" />
                                                </xsl:for-each>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <span class="generated-text">
                                                    <xsl:text>Information not available</xsl:text>
                                                </span>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </div>
                                </div>

                                <div class="row">
                                    <div class="attribute-title col-md-6">
                                        <xsl:text>Ethnicity</xsl:text>
                                    </div>
                                    <div class="col-md-6">
                                        <xsl:choose>
                                            <xsl:when test="n1:patient/n1:ethnicGroupCode">
                                                <xsl:for-each select="n1:patient/n1:ethnicGroupCode">
                                                    <xsl:call-template name="show-race-ethnicity" />
                                                </xsl:for-each>
                                                <!-- SG: 20210510 Added extra ethnicGroupCode-->
                                                <xsl:for-each select="n1:patient/sdtc:ethnicGroupCode">
                                                    <xsl:text>, </xsl:text>
                                                    <xsl:call-template name="show-race-ethnicity" />
                                                </xsl:for-each>
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <span class="generated-text">
                                                    <xsl:text>Information not available</xsl:text>
                                                </span>
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </div>
                                </div>
                            </xsl:if>
                            <!-- SG: 20211019 Added preferred Language -->
                            <div class="row">
                                <div class="attribute-title col-md-6">
                                    <xsl:text>Preferred Language</xsl:text>
                                </div>
                                <div class="col-md-6">
                                    <xsl:choose>
                                        <xsl:when test="n1:patient/n1:languageCommunication/n1:preferenceInd[@value = 'true']">
                                            <xsl:variable name="vPrefLangCount">
                                                <xsl:value-of select="count(n1:patient/n1:languageCommunication/n1:preferenceInd[@value = 'true'])" />
                                            </xsl:variable>
                                            <xsl:for-each select="n1:patient/n1:languageCommunication/n1:preferenceInd[@value = 'true']/preceding-sibling::n1:languageCode">
                                                <xsl:call-template name="show-preferred-language" />
                                                <xsl:if test="$vPrefLangCount > 1 and position() != last()">
                                                    <xsl:text> or </xsl:text>
                                                </xsl:if>
                                            </xsl:for-each>

                                        </xsl:when>
                                        <xsl:otherwise>
                                            <span class="generated-text">
                                                <xsl:text>Information not available</xsl:text>
                                            </span>
                                        </xsl:otherwise>
                                    </xsl:choose>
                                </div>
                            </div>


                        </div>
                    </div>
                    <div class="col-md-6">
                        <h2 class="section-title col-md-6">
                            <xsl:text>Contact</xsl:text>
                        </h2>
                        <div class="header-group-content col-md-8">
                            <xsl:call-template name="show-contactInfo">
                                <xsl:with-param name="contact" select="." />
                            </xsl:call-template>
                        </div>
                    </div>
                </div>
                <!--</xsl:if>-->
                <!-- SG: Added list parent/guardian -->
                <xsl:if test="n1:patient/n1:guardian">
                    <div class="guardian-info container-fluid">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="guardian-name container-fluid">
                                    <h2 class="section-title col-md-6">Parent/Guardian</h2>
                                    <div class="header-group-content col-md-8">
                                        <xsl:call-template name="show-guardian">
                                            <xsl:with-param name="guard" select="n1:patient/n1:guardian" />
                                        </xsl:call-template>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <xsl:if test="n1:patient/n1:guardian/n1:addr | n1:patient/n1:guardian/n1:telecom">
                                    <div class="col-md-6">
                                        <h2 class="section-title col-md-6">Contact</h2>
                                        <div class="header-group-content col-md-8">
                                            <xsl:call-template name="show-contactInfo">
                                                <xsl:with-param name="contact" select="n1:patient/n1:guardian" />
                                            </xsl:call-template>
                                        </div>
                                    </div>
                                </xsl:if>
                            </div>
                        </div>
                    </div>
                </xsl:if>
            </xsl:for-each>
            <!-- list all the emergency contacts -->
            <xsl:if test="n1:participant">
                <xsl:for-each select="n1:participant">
                    <xsl:if test="n1:associatedEntity/@classCode = 'ECON'">
                        <div class="container-fluid" id="emergency-contact">
                            <div class="col-md-6">
                                <h2 class="section-title col-md-6">Emergency Contact</h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:call-template name="show-associatedEntity">
                                        <xsl:with-param name="assoEntity" select="n1:associatedEntity" />
                                    </xsl:call-template>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h2 class="section-title col-md-6">Contact</h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:call-template name="show-contactInfo">
                                        <xsl:with-param name="contact" select="n1:associatedEntity" />
                                    </xsl:call-template>
                                </div>
                            </div>
                        </div>
                    </xsl:if>
                </xsl:for-each>
            </xsl:if>

            <!-- list nex of kin-->
            <xsl:if test="n1:participant">
                <xsl:for-each select="n1:participant">
                    <xsl:if test="n1:associatedEntity/@classCode = 'NOK'">
                        <div class="container-fluid" id="emergency-contact">
                            <div class="col-md-6">
                                <h2 class="section-title col-md-6">Next of Kin</h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:call-template name="show-associatedEntity">
                                        <xsl:with-param name="assoEntity" select="n1:associatedEntity" />
                                    </xsl:call-template>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h2 class="section-title col-md-6">Contact</h2>
                                <div class="header-group-content col-md-8">
                                    <xsl:call-template name="show-contactInfo">
                                        <xsl:with-param name="contact" select="n1:associatedEntity" />
                                    </xsl:call-template>
                                </div>
                            </div>
                        </div>
                    </xsl:if>
                </xsl:for-each>
            </xsl:if>
        </div>

    </xsl:template>
    <!-- relatedDocument -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="relatedDocument">
        <xsl:if test="n1:relatedDocument">
            <table class="header_table">
                <tbody>
                    <xsl:for-each select="n1:relatedDocument">
                        <tr>
                            <td class="td_header_role_name">
                                <span class="td_label">
                                    <xsl:text>Related document</xsl:text>
                                </span>
                            </td>
                            <td class="td_header_role_value">
                                <xsl:for-each select="n1:parentDocument">
                                    <xsl:for-each select="n1:id">
                                        <xsl:call-template name="show-id" />
                                        <br />
                                    </xsl:for-each>
                                </xsl:for-each>
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>
        </xsl:if>
    </xsl:template>
    <!-- authorization (consent) -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="authorization">
        <xsl:if test="n1:authorization">
            <table class="header_table">
                <tbody>
                    <xsl:for-each select="n1:authorization">
                        <tr>
                            <td class="td_header_role_name">
                                <span class="td_label">
                                    <xsl:text>Consent</xsl:text>
                                </span>
                            </td>
                            <td class="td_header_role_value">
                                <xsl:choose>
                                    <xsl:when test="n1:consent/n1:code">
                                        <xsl:call-template name="show-code">
                                            <xsl:with-param name="code" select="n1:consent/n1:code" />
                                        </xsl:call-template>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:call-template name="show-code">
                                            <xsl:with-param name="code" select="n1:consent/n1:statusCode" />
                                        </xsl:call-template>
                                    </xsl:otherwise>
                                </xsl:choose>
                                <br />
                            </td>
                        </tr>
                    </xsl:for-each>
                </tbody>
            </table>
        </xsl:if>
    </xsl:template>
    <!-- setAndVersion -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="setAndVersion">
        <xsl:if test="n1:setId and n1:versionNumber">
            <table class="header_table">
                <tbody>
                    <tr>
                        <td class="td_header_role_name">
                            <xsl:text>SetId and Version</xsl:text>
                        </td>
                        <td class="td_header_role_value">
                            <xsl:text>SetId: </xsl:text>
                            <xsl:call-template name="show-id">
                                <xsl:with-param name="id" select="n1:setId" />
                            </xsl:call-template>
                            <xsl:text>  Version: </xsl:text>
                            <xsl:value-of select="n1:versionNumber/@value" />
                        </td>
                    </tr>
                </tbody>
            </table>
        </xsl:if>
    </xsl:template>
    <!-- show StructuredBody  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:component/n1:structuredBody">
        <xsl:for-each select="n1:component/n1:section">
            <xsl:call-template name="section" />
        </xsl:for-each>
    </xsl:template>
    <!-- show nonXMLBody -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:component/n1:nonXMLBody">
        <xsl:choose>
            <!-- if there is a reference, use that in an IFRAME -->
            <xsl:when test="n1:text/n1:reference">
                <xsl:variable name="source" select="string(n1:text/n1:reference/@value)" />
                <xsl:variable name="mediaType" select="string(n1:text/@mediaType)" />
                <xsl:variable name="lcSource" select="translate($source, $uc, $lc)" />
                <xsl:variable name="scrubbedSource" select="translate($source, $simple-sanitizer-match, $simple-sanitizer-replace)" />
                <xsl:message>
                    <xsl:value-of select="$source" />, <xsl:value-of select="$lcSource" />
                </xsl:message>
                <xsl:choose>
                    <xsl:when test="contains($lcSource, 'javascript')">
                        <p>
                            <xsl:value-of select="$javascript-injection-warning" />
                        </p>
                        <xsl:message>
                            <xsl:value-of select="$javascript-injection-warning" />
                        </xsl:message>
                    </xsl:when>
                    <xsl:when test="not($source = $scrubbedSource)">
                        <p>
                            <xsl:value-of select="$malicious-content-warning" />
                        </p>
                        <xsl:message>
                            <xsl:value-of select="$malicious-content-warning" />
                        </xsl:message>
                    </xsl:when>
                    <xsl:otherwise>
                        <iframe name="nonXMLBody" id="nonXMLBody" WIDTH="80%" HEIGHT="600" src="{$source}">
                            <html>
                                <body>
                                    <object data="{$source}" type="{$mediaType}">
                                        <embed src="{$source}" type="{$mediaType}" />
                                    </object>
                                </body>
                            </html>
                        </iframe>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="n1:text/@mediaType = &quot;text/plain&quot;">
                <pre>
<xsl:value-of select="n1:text/text()" />
</pre>
            </xsl:when>
            <xsl:otherwise>
                <pre>Cannot display the text</pre>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- top level component/section: display title and text,
      and process any nested component/sections
    -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="section">
        <div class="container-fluid header">
            <xsl:call-template name="section-title">
                <xsl:with-param name="title" select="n1:title" />
            </xsl:call-template>
            <xsl:call-template name="section-author" />
            <xsl:call-template name="section-text" />
            <xsl:for-each select="n1:component/n1:section">
                <div class="container-fluid">
                    <xsl:call-template name="nestedSection">
                        <xsl:with-param name="margin" select="2" />
                    </xsl:call-template>
                </div>
            </xsl:for-each>
        </div>
    </xsl:template>
    <!-- top level section title -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="section-title">
        <xsl:param name="title" />
        <h1 class="section-title" id="{generate-id($title)}" ng-click="gotoAnchor('toc')">
            <xsl:value-of select="$title" />
        </h1>
    </xsl:template>

    <!-- section author -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="section-author">
        <xsl:if test="count(n1:author) &gt; 0">
            <div class="section-author">
                <span class="emphasis">
                    <xsl:text>Section Author: </xsl:text>
                </span>
                <xsl:for-each select="n1:author/n1:assignedAuthor">
                    <xsl:choose>
                        <xsl:when test="n1:assignedPerson/n1:name">
                            <xsl:call-template name="show-name">
                                <xsl:with-param name="name" select="n1:assignedPerson/n1:name" />
                            </xsl:call-template>
                            <xsl:if test="n1:representedOrganization">
                                <xsl:text>, </xsl:text>
                                <xsl:call-template name="show-name">
                                    <xsl:with-param name="name" select="n1:representedOrganization/n1:name" />
                                </xsl:call-template>
                            </xsl:if>
                        </xsl:when>
                        <xsl:when test="n1:assignedAuthoringDevice/n1:softwareName">
                            <xsl:call-template name="show-code">
                                <xsl:with-param name="code" select="n1:assignedAuthoringDevice/n1:softwareName" />
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:for-each select="n1:id">
                                <xsl:call-template name="show-id" />
                                <br />
                            </xsl:for-each>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
                <br />
            </div>
        </xsl:if>
    </xsl:template>
    <!-- top-level section Text   -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="section-text">
        <div class="section-text">
            <xsl:apply-templates select="n1:text" />
        </div>
    </xsl:template>
    <!-- nested component/section -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="nestedSection">
        <xsl:param name="margin" />
        <h4>
            <xsl:value-of select="n1:title" />
        </h4>
        <div class="nested-section" style="margin-left : {$margin}em;">
            <xsl:apply-templates select="n1:text" />
        </div>
        <xsl:for-each select="n1:component/n1:section">
            <xsl:call-template name="nestedSection">
                <xsl:with-param name="margin" select="2 * $margin" />
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!--   paragraph  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:paragraph">
        <xsl:element name="p">
            <xsl:call-template name="output-attrs" />
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    <!--   pre format  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:pre">
        <xsl:element name="pre">
            <xsl:call-template name="output-attrs" />
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    <!--   Content w/ deleted text is hidden -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:content[@revised = 'delete']" />
    <!--   content  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:content">
        <xsl:element name="content">
            <xsl:call-template name="output-attrs" />
            <!--<xsl:apply-templates select="@styleCode"/>-->
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    <!-- line break -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:br">
        <xsl:element name="br">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    <!--   list  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:list">
        <xsl:if test="n1:caption">
            <p>
                <b>
                    <xsl:apply-templates select="n1:caption" />
                </b>
            </p>
        </xsl:if>
        <ul>
            <xsl:for-each select="n1:item">
                <li>
                    <xsl:apply-templates />
                </li>
            </xsl:for-each>
        </ul>
    </xsl:template>
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:list[@styleCode = 'none']">
        <xsl:if test="n1:caption">
            <p>
                <b>
                    <xsl:apply-templates select="n1:caption" />
                </b>
            </p>
        </xsl:if>
        <ul style="list-style-type:none">
            <xsl:for-each select="n1:item">
                <li>
                    <xsl:apply-templates />
                </li>
            </xsl:for-each>
        </ul>
    </xsl:template>
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:list[@listType = 'ordered']">
        <xsl:if test="n1:caption">
            <span style="font-weight:bold; ">
                <xsl:apply-templates select="n1:caption" />
            </span>
        </xsl:if>
        <ol>
            <xsl:for-each select="n1:item">
                <li>
                    <xsl:apply-templates />
                </li>
            </xsl:for-each>
        </ol>
    </xsl:template>

    <!--   caption  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:caption">
        <xsl:apply-templates />
        <xsl:text>: </xsl:text>
    </xsl:template>
    <!--  Tables   -->

    <xsl:variable xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="table-elem-attrs">
        <in:tableElems>
            <in:elem name="table">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="summary" />
                <in:attr name="width" />
                <!-- Commented out to keep table rendering consistent -->
                <!--<in:attr name="border"/>-->
                <in:attr name="frame" />
                <in:attr name="rules" />
                <in:attr name="cellspacing" />
                <in:attr name="cellpadding" />
            </in:elem>
            <in:elem name="thead">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="tfoot">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="tbody">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="colgroup">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="span" />
                <in:attr name="width" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="col">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="span" />
                <in:attr name="width" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="tr">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="th">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="abbr" />
                <in:attr name="axis" />
                <in:attr name="headers" />
                <in:attr name="scope" />
                <in:attr name="rowspan" />
                <in:attr name="colspan" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
            <in:elem name="td">
                <in:attr name="ID" />
                <in:attr name="language" />
                <in:attr name="styleCode" />
                <in:attr name="abbr" />
                <in:attr name="axis" />
                <in:attr name="headers" />
                <in:attr name="scope" />
                <in:attr name="rowspan" />
                <in:attr name="colspan" />
                <in:attr name="align" />
                <in:attr name="char" />
                <in:attr name="charoff" />
                <in:attr name="valign" />
            </in:elem>
        </in:tableElems>
    </xsl:variable>

    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="output-attrs">
        <xsl:variable name="elem-name" select="local-name(.)" />
        <!-- This assigns all outputted elements the cda-render class -->
        <!-- <xsl:attribute name="class">cda-render</xsl:attribute>-->
        <xsl:choose>
            <xsl:when test="$elem-name = 'table'">
                <xsl:attribute name="class">table table-striped table-hover</xsl:attribute>
            </xsl:when>
        </xsl:choose>
        <xsl:for-each select="@*">
            <xsl:variable name="attr-name" select="local-name(.)" />
            <xsl:variable name="source" select="." />
            <xsl:variable name="lcSource" select="translate($source, $uc, $lc)" />
            <xsl:variable name="scrubbedSource" select="translate($source, $simple-sanitizer-match, $simple-sanitizer-replace)" />
            <xsl:choose>
                <xsl:when test="contains($lcSource, 'javascript')">
                    <p>
                        <xsl:value-of select="$javascript-injection-warning" />
                    </p>
                    <xsl:message terminate="yes">
                        <xsl:value-of select="$javascript-injection-warning" />
                    </xsl:message>
                </xsl:when>
                <xsl:when test="$attr-name = 'styleCode'">
                    <xsl:apply-templates select="." />
                </xsl:when>
                <!--<xsl:when
          test="not(document('')/xsl:stylesheet/xsl:variable[@name = 'table-elem-attrs']/in:tableElems/in:elem[@name = $elem-name]/in:attr[@name = $attr-name])">
          <xsl:message><xsl:value-of select="$attr-name"/> is not legal in <xsl:value-of
              select="$elem-name"/></xsl:message>
        </xsl:when>-->
                <xsl:when test="not($source = $scrubbedSource)">
                    <p>
                        <xsl:value-of select="$malicious-content-warning" />
                    </p>
                    <xsl:message>
                        <xsl:value-of select="$malicious-content-warning" />
                    </xsl:message>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:copy-of select="." />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>

    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:table">
        <div class="table-responsive">
            <xsl:element name="{local-name()}">
                <xsl:call-template name="output-attrs" />
                <xsl:apply-templates />
            </xsl:element>
        </div>
    </xsl:template>

    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:thead | n1:tfoot | n1:tbody | n1:colgroup | n1:col | n1:tr | n1:th | n1:td">
        <xsl:element name="{local-name()}">
            <xsl:call-template name="output-attrs" />
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>

    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:table/n1:caption">
        <span style="font-weight:bold; ">
            <xsl:apply-templates />
        </span>
    </xsl:template>

    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:linkHtml">
        <xsl:element name="a">
            <xsl:copy-of select="@* | text()" />
        </xsl:element>
    </xsl:template>

    <!--   RenderMultiMedia
     this currently only handles GIF's and JPEG's.  It could, however,
     be extended by including other image MIME types in the predicate
     and/or by generating <object> or <applet> tag with the correct
     params depending on the media type  @ID  =$imageRef  referencedObject
     -->

    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="check-external-image-whitelist">
        <xsl:param name="current-whitelist" />
        <xsl:param name="image-uri" />
        <xsl:choose>
            <xsl:when test="string-length($current-whitelist) &gt; 0">
                <xsl:variable name="whitelist-item">
                    <xsl:choose>
                        <xsl:when test="contains($current-whitelist, '|')">
                            <xsl:value-of select="substring-before($current-whitelist, '|')" />
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$current-whitelist" />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:choose>
                    <xsl:when test="starts-with($image-uri, $whitelist-item)">
                        <br clear="all" />
                        <xsl:element name="img">
                            <xsl:attribute name="src">
                                <xsl:value-of select="$image-uri" />
                            </xsl:attribute>
                        </xsl:element>
                        <xsl:message>
                            <xsl:value-of select="$image-uri" /> is in the whitelist</xsl:message>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="check-external-image-whitelist">
                            <xsl:with-param name="current-whitelist" select="substring-after($current-whitelist, '|')" />
                            <xsl:with-param name="image-uri" select="$image-uri" />
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>

            </xsl:when>
            <xsl:otherwise>
                <p>WARNING: non-local image found <xsl:value-of select="$image-uri" />. Removing. If you wish non-local images preserved please set the limit-external-images param to 'no'.</p>
                <xsl:message>WARNING: non-local image found <xsl:value-of select="$image-uri" />. Removing. If you wish non-local images preserved please set the limit-external-images param to 'no'.</xsl:message>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:renderMultiMedia">
        <xsl:variable name="imageRef" select="@referencedObject" />
        <xsl:choose>
            <xsl:when test="//n1:regionOfInterest[@ID = $imageRef]">
                <!-- Here is where the Region of Interest image referencing goes -->
                <xsl:if test="//n1:regionOfInterest[@ID = $imageRef]//n1:observationMedia/n1:value[@mediaType = 'image/gif' or @mediaType = 'image/jpeg']">
                    <xsl:variable name="image-uri" select="//n1:regionOfInterest[@ID = $imageRef]//n1:observationMedia/n1:value/n1:reference/@value" />

                    <xsl:choose>
                        <xsl:when test="$limit-external-images = 'yes' and (contains($image-uri, ':') or starts-with($image-uri, '\\'))">
                            <xsl:call-template name="check-external-image-whitelist">
                                <xsl:with-param name="current-whitelist" select="$external-image-whitelist" />
                                <xsl:with-param name="image-uri" select="$image-uri" />
                            </xsl:call-template>
                            <!--
                            <p>WARNING: non-local image found <xsl:value-of select="$image-uri"/>. Removing. If you wish non-local images preserved please set the limit-external-images param to 'no'.</p>
                            <xsl:message>WARNING: non-local image found <xsl:value-of select="$image-uri"/>. Removing. If you wish non-local images preserved please set the limit-external-images param to 'no'.</xsl:message>
                            -->
                        </xsl:when>
                        <!--
                        <xsl:when test="$limit-external-images='yes' and starts-with($image-uri,'\\')">
                            <p>WARNING: non-local image found <xsl:value-of select="$image-uri"/></p>
                            <xsl:message>WARNING: non-local image found <xsl:value-of select="$image-uri"/>. Removing. If you wish non-local images preserved please set the limit-external-images param to 'no'.</xsl:message>
                        </xsl:when>
                        -->
                        <xsl:otherwise>
                            <br clear="all" />
                            <xsl:element name="img">
                                <xsl:attribute name="src">
                                    <xsl:value-of select="$image-uri" />
                                </xsl:attribute>
                            </xsl:element>
                        </xsl:otherwise>
                    </xsl:choose>

                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <!-- Here is where the direct MultiMedia image referencing goes -->
                <xsl:if test="//n1:observationMedia[@ID = $imageRef]/n1:value[@mediaType = 'image/gif' or @mediaType = 'image/jpeg']">
                    <br clear="all" />
                    <xsl:element name="img">
                        <xsl:attribute name="src">
                            <xsl:value-of select="//n1:observationMedia[@ID = $imageRef]/n1:value/n1:reference/@value" />
                        </xsl:attribute>
                    </xsl:element>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!--    Stylecode processing
     Supports Bold, Underline and Italics display
     -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="@styleCode">
        <xsl:attribute name="styleCode">
            <xsl:value-of select="." />
        </xsl:attribute>
    </xsl:template>
    <!--    Superscript or Subscript   -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:sup">
        <xsl:element name="sup">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" match="n1:sub">
        <xsl:element name="sub">
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>
    <!-- show-signature -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-sig">
        <xsl:param name="sig" />
        <xsl:choose>
            <xsl:when test="$sig/@code = 'S'">
                <xsl:text>signed</xsl:text>
            </xsl:when>
            <xsl:when test="$sig/@code = 'I'">
                <xsl:text>intended</xsl:text>
            </xsl:when>
            <xsl:when test="$sig/@code = 'X'">
                <xsl:text>signature required</xsl:text>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!--  show-id -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-id">
        <xsl:param name="id" select="." />
        <xsl:choose>
            <xsl:when test="not($id)">
                <xsl:if test="not(@nullFlavor)">
                    <xsl:if test="@extension">
                        <xsl:value-of select="@extension" />
                    </xsl:if>
                    <xsl:text> </xsl:text>
                    <xsl:call-template name="translate-id-type">
                        <xsl:with-param name="id-oid" select="@root" />
                    </xsl:call-template>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:if test="not($id/@nullFlavor)">
                    <xsl:if test="$id/@extension">
                        <xsl:value-of select="$id/@extension" />
                    </xsl:if>
                    <xsl:text> </xsl:text>
                    <xsl:call-template name="translate-id-type">
                        <xsl:with-param name="id-oid" select="$id/@root" />
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- show-name  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-name">
        <xsl:param name="name" />
        <xsl:choose>
            <xsl:when test="$name/n1:family">
                <xsl:if test="$name/n1:prefix">
                    <xsl:value-of select="$name/n1:prefix" />
                    <xsl:text> </xsl:text>
                </xsl:if>
                <xsl:value-of select="$name/n1:given" />
                <xsl:text> </xsl:text>
                <xsl:value-of select="$name/n1:family" />
                <xsl:if test="$name/n1:suffix">
                    <xsl:text>, </xsl:text>
                    <xsl:value-of select="$name/n1:suffix" />
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$name" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- show-gender  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-gender">
        <xsl:choose>
            <xsl:when test="@code = 'M' or @code = 'Male'">
                <xsl:text>Male</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'F' or @code = 'Female'">
                <xsl:text>Female</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'UN' or @code = 'Undifferentiated'">
                <xsl:text>Undifferentiated</xsl:text>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- show-race-ethnicity  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-race-ethnicity">
        <xsl:choose>
            <xsl:when test="@displayName">
                <xsl:value-of select="@displayName" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="@code" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- show-preferred-language  -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-preferred-language">
        <xsl:choose>
            <xsl:when test="@displayName">
                <xsl:value-of select="@displayName" />
            </xsl:when>
            <xsl:when test="@code = 'ar'">
                <xsl:text>Arabic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bn'">
                <xsl:text>Bengali</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cs'">
                <xsl:text>Czech</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'da'">
                <xsl:text>Danish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'de'">
                <xsl:text>German</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'de-AT'">
                <xsl:text>German (Austria)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'de-CH'">
                <xsl:text>German (Switzerland)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'de-DE'">
                <xsl:text>German (Germany)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'el'">
                <xsl:text>Greek</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en'">
                <xsl:text>English</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-AU'">
                <xsl:text>English (Australia)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-CA'">
                <xsl:text>English (Canada)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-GB'">
                <xsl:text>English (Great Britain)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-IN'">
                <xsl:text>English (India)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-NZ'">
                <xsl:text>English (New Zeland)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-SG'">
                <xsl:text>English (Singapore)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'en-US'">
                <xsl:text>English (United States)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'es'">
                <xsl:text>Spanish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'es-AR'">
                <xsl:text>Spanish (Argentina)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'es-ES'">
                <xsl:text>Spanish (Spain)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'es-UY'">
                <xsl:text>Spanish (Uruguay)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fi'">
                <xsl:text>Finnish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fr'">
                <xsl:text>French</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fr-BE'">
                <xsl:text>French (Belgium)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fr-CH'">
                <xsl:text>French (Switzerland)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fr-FR'">
                <xsl:text>French (France)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fy'">
                <xsl:text>Frysian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fy-NL'">
                <xsl:text>Frysian (Netherlands)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hi'">
                <xsl:text>Hindi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hr'">
                <xsl:text>Croatian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'it'">
                <xsl:text>Italian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'it-CH'">
                <xsl:text>Italian (Switzerland)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'it-IT'">
                <xsl:text>Italian (Italy)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ja'">
                <xsl:text>Japanese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ko'">
                <xsl:text>Korean</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nl'">
                <xsl:text>Dutch</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nl-BE'">
                <xsl:text>Dutch (Belgium)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nl-NL'">
                <xsl:text>Dutch (Netherlands)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'no'">
                <xsl:text>Norwegian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'no-NO'">
                <xsl:text>Norwegian (Norway)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pa'">
                <xsl:text>Punjabi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pl'">
                <xsl:text>Polish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pt'">
                <xsl:text>Portuguese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pt-BR'">
                <xsl:text>Portuguese (Brazil)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ru'">
                <xsl:text>Russian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ru-RU'">
                <xsl:text>Russian (Russia)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sr'">
                <xsl:text>Serbian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sr-RS'">
                <xsl:text>Serbian (Serbia)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sv'">
                <xsl:text>Swedish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sv-SE'">
                <xsl:text>Swedish (Sweden)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'te'">
                <xsl:text>Telegu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zh'">
                <xsl:text>Chinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zh-CN'">
                <xsl:text>Chinese (China)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zh-HK'">
                <xsl:text>Chinese (Hong Kong)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zh-SG'">
                <xsl:text>Chinese (Singapore)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zh-TW'">
                <xsl:text>Chinese (Taiwan)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'aar'">
                <xsl:text>Afar</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'abk'">
                <xsl:text>Abkhazian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ace'">
                <xsl:text>Achinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ach'">
                <xsl:text>Acoli</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ada'">
                <xsl:text>Adangme</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ady'">
                <xsl:text>Adyghe; Adygei</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'afa'">
                <xsl:text>Afro-Asiatic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'afh'">
                <xsl:text>Afrihili</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'afr'">
                <xsl:text>Afrikaans</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ain'">
                <xsl:text>Ainu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'aka'">
                <xsl:text>Akan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'akk'">
                <xsl:text>Akkadian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'alb (B)'">
                <xsl:text>Albanian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sqi (T)'">
                <xsl:text>Albanian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ale'">
                <xsl:text>Aleut</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'alg'">
                <xsl:text>Algonquian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'alt'">
                <xsl:text>Southern Altai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'amh'">
                <xsl:text>Amharic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ang'">
                <xsl:text>English, Old (ca.450-1100)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'anp'">
                <xsl:text>Angika</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'apa'">
                <xsl:text>Apache languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ara'">
                <xsl:text>Arabic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arc'">
                <xsl:text>Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arg'">
                <xsl:text>Aragonese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arm (B)'">
                <xsl:text>Armenian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hye (T)'">
                <xsl:text>Armenian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arn'">
                <xsl:text>Mapudungun; Mapuche</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arp'">
                <xsl:text>Arapaho</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'art'">
                <xsl:text>Artificial languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arw'">
                <xsl:text>Arawak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'asm'">
                <xsl:text>Assamese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ast'">
                <xsl:text>Asturian; Bable; Leonese; Asturleonese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ath'">
                <xsl:text>Athapascan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'aus'">
                <xsl:text>Australian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ava'">
                <xsl:text>Avaric</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ave'">
                <xsl:text>Avestan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'awa'">
                <xsl:text>Awadhi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'aym'">
                <xsl:text>Aymara</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'aze'">
                <xsl:text>Azerbaijani</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bad'">
                <xsl:text>Banda languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bai'">
                <xsl:text>Bamileke languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bak'">
                <xsl:text>Bashkir</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bal'">
                <xsl:text>Baluchi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bam'">
                <xsl:text>Bambara</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ban'">
                <xsl:text>Balinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'baq (B)'">
                <xsl:text>Basque</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'eus (T)'">
                <xsl:text>Basque</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bas'">
                <xsl:text>Basa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bat'">
                <xsl:text>Baltic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bej'">
                <xsl:text>Beja; Bedawiyet</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bel'">
                <xsl:text>Belarusian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bem'">
                <xsl:text>Bemba</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ben'">
                <xsl:text>Bengali</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ber'">
                <xsl:text>Berber languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bho'">
                <xsl:text>Bhojpuri</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bih'">
                <xsl:text>Bihari languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bik'">
                <xsl:text>Bikol</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bin'">
                <xsl:text>Bini; Edo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bis'">
                <xsl:text>Bislama</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bla'">
                <xsl:text>Siksika</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bnt'">
                <xsl:text>Bantu languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tib (B)'">
                <xsl:text>Tibetan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bod (T)'">
                <xsl:text>Tibetan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bos'">
                <xsl:text>Bosnian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bra'">
                <xsl:text>Braj</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bre'">
                <xsl:text>Breton</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'btk'">
                <xsl:text>Batak languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bua'">
                <xsl:text>Buriat</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bug'">
                <xsl:text>Buginese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bul'">
                <xsl:text>Bulgarian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bur (B)'">
                <xsl:text>Burmese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mya (T)'">
                <xsl:text>Burmese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'byn'">
                <xsl:text>Blin; Bilin</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cad'">
                <xsl:text>Caddo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cai'">
                <xsl:text>Central American Indian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'car'">
                <xsl:text>Galibi Carib</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cat'">
                <xsl:text>Catalan; Valencian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cau'">
                <xsl:text>Caucasian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ceb'">
                <xsl:text>Cebuano</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cel'">
                <xsl:text>Celtic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cze (B)'">
                <xsl:text>Czech</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ces (T)'">
                <xsl:text>Czech</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cha'">
                <xsl:text>Chamorro</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chb'">
                <xsl:text>Chibcha</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'che'">
                <xsl:text>Chechen</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chg'">
                <xsl:text>Chagatai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chi (B)'">
                <xsl:text>Chinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zho (T)'">
                <xsl:text>Chinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chk'">
                <xsl:text>Chuukese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chm'">
                <xsl:text>Mari</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chn'">
                <xsl:text>Chinook jargon</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cho'">
                <xsl:text>Choctaw</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chp'">
                <xsl:text>Chipewyan; Dene Suline</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chr'">
                <xsl:text>Cherokee</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chu'">
                <xsl:text>Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chv'">
                <xsl:text>Chuvash</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chy'">
                <xsl:text>Cheyenne</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cmc'">
                <xsl:text>Chamic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cnr'">
                <xsl:text>Montenegrin</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cop'">
                <xsl:text>Coptic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cor'">
                <xsl:text>Cornish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cos'">
                <xsl:text>Corsican</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cpe'">
                <xsl:text>Creoles and pidgins, English based</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cpf'">
                <xsl:text>Creoles and pidgins, French-based</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cpp'">
                <xsl:text>Creoles and pidgins, Portuguese-based</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cre'">
                <xsl:text>Cree</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'crh'">
                <xsl:text>Crimean Tatar; Crimean Turkish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'crp'">
                <xsl:text>Creoles and pidgins</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'csb'">
                <xsl:text>Kashubian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cus'">
                <xsl:text>Cushitic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wel (B)'">
                <xsl:text>Welsh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cym (T)'">
                <xsl:text>Welsh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cze (B)'">
                <xsl:text>Czech</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ces (T)'">
                <xsl:text>Czech</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dak'">
                <xsl:text>Dakota</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dan'">
                <xsl:text>Danish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dar'">
                <xsl:text>Dargwa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'day'">
                <xsl:text>Land Dayak languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'del'">
                <xsl:text>Delaware</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'den'">
                <xsl:text>Slave (Athapascan)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ger (B)'">
                <xsl:text>German</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'deu (T)'">
                <xsl:text>German</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dgr'">
                <xsl:text>Tlicho; Dogrib</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'din'">
                <xsl:text>Dinka</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'div'">
                <xsl:text>Divehi; Dhivehi; Maldivian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'doi'">
                <xsl:text>Dogri (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dra'">
                <xsl:text>Dravidian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dsb'">
                <xsl:text>Lower Sorbian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dua'">
                <xsl:text>Duala</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dum'">
                <xsl:text>Dutch, Middle (ca.1050-1350)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dut (B)'">
                <xsl:text>Dutch; Flemish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nld (T)'">
                <xsl:text>Dutch; Flemish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dyu'">
                <xsl:text>Dyula</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dzo'">
                <xsl:text>Dzongkha</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'efi'">
                <xsl:text>Efik</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'egy'">
                <xsl:text>Egyptian (Ancient)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'eka'">
                <xsl:text>Ekajuk</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gre (B)'">
                <xsl:text>Greek, Modern (1453-)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ell (T)'">
                <xsl:text>Greek, Modern (1453-)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'elx'">
                <xsl:text>Elamite</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'eng'">
                <xsl:text>English</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'enm'">
                <xsl:text>English, Middle (1100-1500)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'epo'">
                <xsl:text>Esperanto</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'est'">
                <xsl:text>Estonian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'baq (B)'">
                <xsl:text>Basque</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'eus (T)'">
                <xsl:text>Basque</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ewe'">
                <xsl:text>Ewe</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ewo'">
                <xsl:text>Ewondo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fan'">
                <xsl:text>Fang</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fao'">
                <xsl:text>Faroese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'per (B)'">
                <xsl:text>Persian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fas (T)'">
                <xsl:text>Persian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fat'">
                <xsl:text>Fanti</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fij'">
                <xsl:text>Fijian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fil'">
                <xsl:text>Filipino; Pilipino</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fin'">
                <xsl:text>Finnish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fiu'">
                <xsl:text>Finno-Ugrian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fon'">
                <xsl:text>Fon</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fre (B)'">
                <xsl:text>French</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fra (T)'">
                <xsl:text>French</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fre (B)'">
                <xsl:text>French</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fra (T)'">
                <xsl:text>French</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'frm'">
                <xsl:text>French, Middle (ca.1400-1600)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fro'">
                <xsl:text>French, Old (842-ca.1400)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'frr'">
                <xsl:text>Northern Frisian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'frs'">
                <xsl:text>Eastern Frisian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fry'">
                <xsl:text>Western Frisian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ful'">
                <xsl:text>Fulah</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fur'">
                <xsl:text>Friulian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gaa'">
                <xsl:text>Ga</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gay'">
                <xsl:text>Gayo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gba'">
                <xsl:text>Gbaya</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gem'">
                <xsl:text>Germanic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'geo (B)'">
                <xsl:text>Georgian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kat (T)'">
                <xsl:text>Georgian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ger (B)'">
                <xsl:text>German</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'deu (T)'">
                <xsl:text>German</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gez'">
                <xsl:text>Geez</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gil'">
                <xsl:text>Gilbertese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gla'">
                <xsl:text>Gaelic; Scottish Gaelic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gle'">
                <xsl:text>Irish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'glg'">
                <xsl:text>Galician</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'glv'">
                <xsl:text>Manx</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gmh'">
                <xsl:text>German, Middle High (ca.1050-1500)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'goh'">
                <xsl:text>German, Old High (ca.750-1050)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gon'">
                <xsl:text>Gondi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gor'">
                <xsl:text>Gorontalo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'got'">
                <xsl:text>Gothic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'grb'">
                <xsl:text>Grebo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'grc'">
                <xsl:text>Greek, Ancient (to 1453)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gre (B)'">
                <xsl:text>Greek, Modern (1453-)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ell (T)'">
                <xsl:text>Greek, Modern (1453-)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'grn'">
                <xsl:text>Guarani</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gsw'">
                <xsl:text>Swiss German; Alemannic; Alsatian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'guj'">
                <xsl:text>Gujarati</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'gwi'">
                <xsl:text>Gwich'in</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hai'">
                <xsl:text>Haida</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hat'">
                <xsl:text>Haitian; Haitian Creole</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hau'">
                <xsl:text>Hausa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'haw'">
                <xsl:text>Hawaiian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'heb'">
                <xsl:text>Hebrew</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'her'">
                <xsl:text>Herero</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hil'">
                <xsl:text>Hiligaynon</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'him'">
                <xsl:text>Himachali languages; Western Pahari languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hin'">
                <xsl:text>Hindi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hit'">
                <xsl:text>Hittite</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hmn'">
                <xsl:text>Hmong; Mong</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hmo'">
                <xsl:text>Hiri Motu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hrv'">
                <xsl:text>Croatian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hsb'">
                <xsl:text>Upper Sorbian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hun'">
                <xsl:text>Hungarian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hup'">
                <xsl:text>Hupa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'arm (B)'">
                <xsl:text>Armenian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'hye (T)'">
                <xsl:text>Armenian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'iba'">
                <xsl:text>Iban</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ibo'">
                <xsl:text>Igbo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ice (B)'">
                <xsl:text>Icelandic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'isl (T)'">
                <xsl:text>Icelandic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ido'">
                <xsl:text>Ido</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'iii'">
                <xsl:text>Sichuan Yi; Nuosu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ijo'">
                <xsl:text>Ijo languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'iku'">
                <xsl:text>Inuktitut</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ile'">
                <xsl:text>Interlingue; Occidental</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ilo'">
                <xsl:text>Iloko</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ina'">
                <xsl:text>Interlingua (International Auxiliary Language Association)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'inc'">
                <xsl:text>Indic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ind'">
                <xsl:text>Indonesian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ine'">
                <xsl:text>Indo-European languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'inh'">
                <xsl:text>Ingush</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ipk'">
                <xsl:text>Inupiaq</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ira'">
                <xsl:text>Iranian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'iro'">
                <xsl:text>Iroquoian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ice (B)'">
                <xsl:text>Icelandic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'isl (T)'">
                <xsl:text>Icelandic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ita'">
                <xsl:text>Italian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'jav'">
                <xsl:text>Javanese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'jbo'">
                <xsl:text>Lojban</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'jpn'">
                <xsl:text>Japanese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'jpr'">
                <xsl:text>Judeo-Persian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'jrb'">
                <xsl:text>Judeo-Arabic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kaa'">
                <xsl:text>Kara-Kalpak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kab'">
                <xsl:text>Kabyle</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kac'">
                <xsl:text>Kachin; Jingpho</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kal'">
                <xsl:text>Kalaallisut; Greenlandic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kam'">
                <xsl:text>Kamba</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kan'">
                <xsl:text>Kannada</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kar'">
                <xsl:text>Karen languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kas'">
                <xsl:text>Kashmiri</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'geo (B)'">
                <xsl:text>Georgian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kat (T)'">
                <xsl:text>Georgian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kau'">
                <xsl:text>Kanuri</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kaw'">
                <xsl:text>Kawi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kaz'">
                <xsl:text>Kazakh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kbd'">
                <xsl:text>Kabardian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kha'">
                <xsl:text>Khasi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'khi'">
                <xsl:text>Khoisan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'khm'">
                <xsl:text>Central Khmer</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kho'">
                <xsl:text>Khotanese; Sakan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kik'">
                <xsl:text>Kikuyu; Gikuyu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kin'">
                <xsl:text>Kinyarwanda</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kir'">
                <xsl:text>Kirghiz; Kyrgyz</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kmb'">
                <xsl:text>Kimbundu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kok'">
                <xsl:text>Konkani (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kom'">
                <xsl:text>Komi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kon'">
                <xsl:text>Kongo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kor'">
                <xsl:text>Korean</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kos'">
                <xsl:text>Kosraean</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kpe'">
                <xsl:text>Kpelle</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'krc'">
                <xsl:text>Karachay-Balkar</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'krl'">
                <xsl:text>Karelian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kro'">
                <xsl:text>Kru languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kru'">
                <xsl:text>Kurukh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kua'">
                <xsl:text>Kuanyama; Kwanyama</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kum'">
                <xsl:text>Kumyk</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kur'">
                <xsl:text>Kurdish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'kut'">
                <xsl:text>Kutenai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lad'">
                <xsl:text>Ladino</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lah'">
                <xsl:text>Lahnda</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lam'">
                <xsl:text>Lamba</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lao'">
                <xsl:text>Lao</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lat'">
                <xsl:text>Latin</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lav'">
                <xsl:text>Latvian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lez'">
                <xsl:text>Lezghian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lim'">
                <xsl:text>Limburgan; Limburger; Limburgish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lin'">
                <xsl:text>Lingala</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lit'">
                <xsl:text>Lithuanian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lol'">
                <xsl:text>Mongo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'loz'">
                <xsl:text>Lozi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ltz'">
                <xsl:text>Luxembourgish; Letzeburgesch</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lua'">
                <xsl:text>Luba-Lulua</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lub'">
                <xsl:text>Luba-Katanga</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lug'">
                <xsl:text>Ganda</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lui'">
                <xsl:text>Luiseno</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lun'">
                <xsl:text>Lunda</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'luo'">
                <xsl:text>Luo (Kenya and Tanzania)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'lus'">
                <xsl:text>Lushai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mac (B)'">
                <xsl:text>Macedonian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mkd (T)'">
                <xsl:text>Macedonian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mad'">
                <xsl:text>Madurese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mag'">
                <xsl:text>Magahi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mah'">
                <xsl:text>Marshallese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mai'">
                <xsl:text>Maithili</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mak'">
                <xsl:text>Makasar</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mal'">
                <xsl:text>Malayalam</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'man'">
                <xsl:text>Mandingo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mao (B)'">
                <xsl:text>Maori</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mri (T)'">
                <xsl:text>Maori</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'map'">
                <xsl:text>Austronesian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mar'">
                <xsl:text>Marathi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mas'">
                <xsl:text>Masai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'may (B)'">
                <xsl:text>Malay (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'msa (T)'">
                <xsl:text>Malay (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mdf'">
                <xsl:text>Moksha</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mdr'">
                <xsl:text>Mandar</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'men'">
                <xsl:text>Mende</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mga'">
                <xsl:text>Irish, Middle (900-1200)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mic'">
                <xsl:text>Mi'kmaq; Micmac</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'min'">
                <xsl:text>Minangkabau</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mis'">
                <xsl:text>Uncoded languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mac (B)'">
                <xsl:text>Macedonian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mkd (T)'">
                <xsl:text>Macedonian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mkh'">
                <xsl:text>Mon-Khmer languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mlg'">
                <xsl:text>Malagasy</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mlt'">
                <xsl:text>Maltese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mnc'">
                <xsl:text>Manchu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mni'">
                <xsl:text>Manipuri</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mno'">
                <xsl:text>Manobo languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'moh'">
                <xsl:text>Mohawk</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mon'">
                <xsl:text>Mongolian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mos'">
                <xsl:text>Mossi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mao (B)'">
                <xsl:text>Maori</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mri (T)'">
                <xsl:text>Maori</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'may (B)'">
                <xsl:text>Malay (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'msa (T)'">
                <xsl:text>Malay (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mul'">
                <xsl:text>Multiple languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mun'">
                <xsl:text>Munda languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mus'">
                <xsl:text>Creek</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mwl'">
                <xsl:text>Mirandese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mwr'">
                <xsl:text>Marwari</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bur (B)'">
                <xsl:text>Burmese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'mya (T)'">
                <xsl:text>Burmese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'myn'">
                <xsl:text>Mayan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'myv'">
                <xsl:text>Erzya</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nah'">
                <xsl:text>Nahuatl languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nai'">
                <xsl:text>North American Indian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nap'">
                <xsl:text>Neapolitan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nau'">
                <xsl:text>Nauru</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nav'">
                <xsl:text>Navajo; Navaho</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nbl'">
                <xsl:text>Ndebele, South; South Ndebele</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nde'">
                <xsl:text>Ndebele, North; North Ndebele</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ndo'">
                <xsl:text>Ndonga</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nds'">
                <xsl:text>Low German; Low Saxon; German, Low; Saxon, Low</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nep'">
                <xsl:text>Nepali (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'new'">
                <xsl:text>Nepal Bhasa; Newari</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nia'">
                <xsl:text>Nias</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nic'">
                <xsl:text>Niger-Kordofanian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'niu'">
                <xsl:text>Niuean</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'dut (B)'">
                <xsl:text>Dutch; Flemish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nld (T)'">
                <xsl:text>Dutch; Flemish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nno'">
                <xsl:text>Norwegian Nynorsk; Nynorsk, Norwegian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nob'">
                <xsl:text>Bokmål, Norwegian; Norwegian Bokmål</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nog'">
                <xsl:text>Nogai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'non'">
                <xsl:text>Norse, Old</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nor'">
                <xsl:text>Norwegian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nqo'">
                <xsl:text>N'Ko</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nso'">
                <xsl:text>Pedi; Sepedi; Northern Sotho</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nub'">
                <xsl:text>Nubian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nwc'">
                <xsl:text>Classical Newari; Old Newari; Classical Nepal Bhasa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nya'">
                <xsl:text>Chichewa; Chewa; Nyanja</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nym'">
                <xsl:text>Nyamwezi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nyn'">
                <xsl:text>Nyankole</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nyo'">
                <xsl:text>Nyoro</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'nzi'">
                <xsl:text>Nzima</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'oci'">
                <xsl:text>Occitan (post 1500)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'oji'">
                <xsl:text>Ojibwa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ori'">
                <xsl:text>Oriya (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'orm'">
                <xsl:text>Oromo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'osa'">
                <xsl:text>Osage</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'oss'">
                <xsl:text>Ossetian; Ossetic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ota'">
                <xsl:text>Turkish, Ottoman (1500-1928)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'oto'">
                <xsl:text>Otomian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'paa'">
                <xsl:text>Papuan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pag'">
                <xsl:text>Pangasinan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pal'">
                <xsl:text>Pahlavi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pam'">
                <xsl:text>Pampanga; Kapampangan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pan'">
                <xsl:text>Panjabi; Punjabi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pap'">
                <xsl:text>Papiamento</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pau'">
                <xsl:text>Palauan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'peo'">
                <xsl:text>Persian, Old (ca.600-400 B.C.)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'per (B)'">
                <xsl:text>Persian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'fas (T)'">
                <xsl:text>Persian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'phi'">
                <xsl:text>Philippine languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'phn'">
                <xsl:text>Phoenician</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pli'">
                <xsl:text>Pali</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pol'">
                <xsl:text>Polish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pon'">
                <xsl:text>Pohnpeian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'por'">
                <xsl:text>Portuguese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pra'">
                <xsl:text>Prakrit languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pro'">
                <xsl:text>Provençal, Old (to 1500);Occitan, Old (to 1500)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'pus'">
                <xsl:text>Pushto; Pashto</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'qaa-qtz'">
                <xsl:text>Reserved for local use</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'que'">
                <xsl:text>Quechua</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'raj'">
                <xsl:text>Rajasthani</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rap'">
                <xsl:text>Rapanui</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rar'">
                <xsl:text>Rarotongan; Cook Islands Maori</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'roa'">
                <xsl:text>Romance languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'roh'">
                <xsl:text>Romansh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rom'">
                <xsl:text>Romany</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rum (B)'">
                <xsl:text>Romanian; Moldavian; Moldovan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ron (T)'">
                <xsl:text>Romanian; Moldavian; Moldovan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rum (B)'">
                <xsl:text>Romanian; Moldavian; Moldovan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ron (T)'">
                <xsl:text>Romanian; Moldavian; Moldovan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'run'">
                <xsl:text>Rundi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rup'">
                <xsl:text>Aromanian; Arumanian; Macedo-Romanian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'rus'">
                <xsl:text>Russian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sad'">
                <xsl:text>Sandawe</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sag'">
                <xsl:text>Sango</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sah'">
                <xsl:text>Yakut</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sai'">
                <xsl:text>South American Indian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sal'">
                <xsl:text>Salishan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sam'">
                <xsl:text>Samaritan Aramaic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'san'">
                <xsl:text>Sanskrit</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sas'">
                <xsl:text>Sasak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sat'">
                <xsl:text>Santali</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'scn'">
                <xsl:text>Sicilian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sco'">
                <xsl:text>Scots</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sel'">
                <xsl:text>Selkup</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sem'">
                <xsl:text>Semitic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sga'">
                <xsl:text>Irish, Old (to 900)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sgn'">
                <xsl:text>Sign Languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'shn'">
                <xsl:text>Shan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sid'">
                <xsl:text>Sidamo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sin'">
                <xsl:text>Sinhala; Sinhalese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sio'">
                <xsl:text>Siouan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sit'">
                <xsl:text>Sino-Tibetan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sla'">
                <xsl:text>Slavic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'slo (B)'">
                <xsl:text>Slovak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'slk (T)'">
                <xsl:text>Slovak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'slo (B)'">
                <xsl:text>Slovak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'slk (T)'">
                <xsl:text>Slovak</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'slv'">
                <xsl:text>Slovenian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sma'">
                <xsl:text>Southern Sami</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sme'">
                <xsl:text>Northern Sami</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'smi'">
                <xsl:text>Sami languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'smj'">
                <xsl:text>Lule Sami</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'smn'">
                <xsl:text>Inari Sami</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'smo'">
                <xsl:text>Samoan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sms'">
                <xsl:text>Skolt Sami</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sna'">
                <xsl:text>Shona</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'snd'">
                <xsl:text>Sindhi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'snk'">
                <xsl:text>Soninke</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sog'">
                <xsl:text>Sogdian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'som'">
                <xsl:text>Somali</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'son'">
                <xsl:text>Songhai languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sot'">
                <xsl:text>Sotho, Southern</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'spa'">
                <xsl:text>Spanish; Castilian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'alb (B)'">
                <xsl:text>Albanian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sqi (T)'">
                <xsl:text>Albanian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'srd'">
                <xsl:text>Sardinian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'srn'">
                <xsl:text>Sranan Tongo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'srp'">
                <xsl:text>Serbian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'srr'">
                <xsl:text>Serer</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ssa'">
                <xsl:text>Nilo-Saharan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ssw'">
                <xsl:text>Swati</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'suk'">
                <xsl:text>Sukuma</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sun'">
                <xsl:text>Sundanese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sus'">
                <xsl:text>Susu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'sux'">
                <xsl:text>Sumerian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'swa'">
                <xsl:text>Swahili (macrolanguage)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'swe'">
                <xsl:text>Swedish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'syc'">
                <xsl:text>Classical Syriac</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'syr'">
                <xsl:text>Syriac</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tah'">
                <xsl:text>Tahitian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tai'">
                <xsl:text>Tai languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tam'">
                <xsl:text>Tamil</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tat'">
                <xsl:text>Tatar</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tel'">
                <xsl:text>Telugu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tem'">
                <xsl:text>Timne</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ter'">
                <xsl:text>Tereno</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tet'">
                <xsl:text>Tetum</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tgk'">
                <xsl:text>Tajik</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tgl'">
                <xsl:text>Tagalog</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tha'">
                <xsl:text>Thai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tib (B)'">
                <xsl:text>Tibetan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'bod (T)'">
                <xsl:text>Tibetan</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tig'">
                <xsl:text>Tigre</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tir'">
                <xsl:text>Tigrinya</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tiv'">
                <xsl:text>Tiv</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tkl'">
                <xsl:text>Tokelau</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tlh'">
                <xsl:text>Klingon; tlhIngan-Hol</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tli'">
                <xsl:text>Tlingit</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tmh'">
                <xsl:text>Tamashek</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tog'">
                <xsl:text>Tonga (Nyasa)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ton'">
                <xsl:text>Tonga (Tonga Islands)</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tpi'">
                <xsl:text>Tok Pisin</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tsi'">
                <xsl:text>Tsimshian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tsn'">
                <xsl:text>Tswana</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tso'">
                <xsl:text>Tsonga</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tuk'">
                <xsl:text>Turkmen</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tum'">
                <xsl:text>Tumbuka</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tup'">
                <xsl:text>Tupi languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tur'">
                <xsl:text>Turkish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tut'">
                <xsl:text>Altaic languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tvl'">
                <xsl:text>Tuvalu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'twi'">
                <xsl:text>Twi</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'tyv'">
                <xsl:text>Tuvinian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'udm'">
                <xsl:text>Udmurt</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'uga'">
                <xsl:text>Ugaritic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'uig'">
                <xsl:text>Uighur; Uyghur</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ukr'">
                <xsl:text>Ukrainian</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'umb'">
                <xsl:text>Umbundu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'und'">
                <xsl:text>Undetermined</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'urd'">
                <xsl:text>Urdu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'uzb'">
                <xsl:text>Uzbek</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'vai'">
                <xsl:text>Vai</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ven'">
                <xsl:text>Venda</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'vie'">
                <xsl:text>Vietnamese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'vol'">
                <xsl:text>Volapük</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'vot'">
                <xsl:text>Votic</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wak'">
                <xsl:text>Wakashan languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wal'">
                <xsl:text>Wolaitta; Wolaytta</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'war'">
                <xsl:text>Waray</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'was'">
                <xsl:text>Washo</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wel (B)'">
                <xsl:text>Welsh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'cym (T)'">
                <xsl:text>Welsh</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wen'">
                <xsl:text>Sorbian languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wln'">
                <xsl:text>Walloon</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'wol'">
                <xsl:text>Wolof</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'xal'">
                <xsl:text>Kalmyk; Oirat</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'xho'">
                <xsl:text>Xhosa</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'yao'">
                <xsl:text>Yao</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'yap'">
                <xsl:text>Yapese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'yid'">
                <xsl:text>Yiddish</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'yor'">
                <xsl:text>Yoruba</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'ypk'">
                <xsl:text>Yupik languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zap'">
                <xsl:text>Zapotec</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zbl'">
                <xsl:text>Blissymbols; Blissymbolics; Bliss</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zen'">
                <xsl:text>Zenaga</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zgh'">
                <xsl:text>Standard Moroccan Tamazight</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zha'">
                <xsl:text>Zhuang; Chuang</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'chi (B)'">
                <xsl:text>Chinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zho (T)'">
                <xsl:text>Chinese</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'znd'">
                <xsl:text>Zande languages</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zul'">
                <xsl:text>Zulu</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zun'">
                <xsl:text>Zuni</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zxx'">
                <xsl:text>No linguistic content; Not applicable</xsl:text>
            </xsl:when>
            <xsl:when test="@code = 'zza'">
                <xsl:text>Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="@code" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- show-contactInfo -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-contactInfo">
        <xsl:param name="contact" />
        <xsl:variable name="vAddrCount">
            <xsl:value-of
                select="count($contact/n1:addr[string-length(n1:streetAddressLine) > 0 or string-length(n1:streetName) > 0 or string-length(n1:houseNumber) > 0 or string-length(n1:city) > 0 or string-length(n1:state) > 0 or string-length(n1:postalCode) > 0 or string-length(n1:county) > 0 or string-length(n1:country) > 0])"
             />
        </xsl:variable>
        <xsl:for-each select="$contact/n1:addr[string-length(n1:streetAddressLine) > 0 or string-length(n1:streetName) > 0 or string-length(n1:houseNumber) > 0 or string-length(n1:city) > 0 or string-length(n1:state) > 0 or string-length(n1:postalCode) > 0 or string-length(n1:county) > 0 or string-length(n1:country) > 0]">
            <xsl:call-template name="show-address">
                <xsl:with-param name="address" select="." />
            </xsl:call-template>
            <xsl:if test="$vAddrCount > 1 and position() != last()">
                <br />
            </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$contact/n1:telecom">
            <xsl:call-template name="show-telecom">
                <xsl:with-param name="telecom" select="." />
            </xsl:call-template>
        </xsl:for-each>
    </xsl:template>
    <!-- show-address -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-address">
        <xsl:param name="address" />
        <div class="address-group">
            <xsl:choose>
                <xsl:when test="$address">
                    <div class="adress-group-header">
                        <xsl:if test="$address/@use">
                            <xsl:call-template name="translateTelecomCode">
                                <xsl:with-param name="code" select="$address/@use" />
                            </xsl:call-template>
                        </xsl:if>
                        <!-- SG: 20211020 Added processing for useable period -->
                        <xsl:if test="$address/n1:useablePeriod">
                            <xsl:text> (</xsl:text>
                            <xsl:call-template name="show-time">
                                <xsl:with-param name="datetime" select="$address/n1:useablePeriod/n1:low" />
                            </xsl:call-template>
                            <xsl:text> to </xsl:text>
                            <xsl:choose>
                                <xsl:when test="$address/n1:useablePeriod/n1:high">
                                    <xsl:call-template name="show-time">
                                        <xsl:with-param name="datetime" select="$address/n1:useablePeriod/n1:high" />
                                    </xsl:call-template>
                                </xsl:when>
                                <xsl:otherwise>present</xsl:otherwise>
                            </xsl:choose>
                            <xsl:text>)</xsl:text>
                        </xsl:if>
                    </div>
                    <div class="address-group-content">
                        <p class="tight">
                            <xsl:for-each select="$address/n1:streetAddressLine">
                                <xsl:value-of select="." />
                                <xsl:text> </xsl:text>
                            </xsl:for-each>
                            <xsl:if test="$address/n1:streetName">
                                <xsl:value-of select="$address/n1:streetName" />
                                <xsl:text> </xsl:text>
                                <xsl:value-of select="$address/n1:houseNumber" />
                            </xsl:if>
                        </p>
                        <p class="tight">
                            <xsl:if test="string-length($address/n1:city) &gt; 0">
                                <xsl:value-of select="$address/n1:city" />
                            </xsl:if>
                            <xsl:if test="string-length($address/n1:state) &gt; 0">
                                <xsl:text>, </xsl:text>
                                <xsl:value-of select="$address/n1:state" />
                            </xsl:if>
                        </p>
                        <p class="tight">
                            <xsl:if test="string-length($address/n1:postalCode) &gt; 0">
                                <!--<xsl:text>&#160;</xsl:text>-->
                                <xsl:value-of select="$address/n1:postalCode" />
                            </xsl:if>
                            <xsl:if test="string-length($address/n1:country) &gt; 0">
                                <xsl:if test="string-length($address/n1:postalCode) &gt; 0">
                                    <xsl:text>, </xsl:text>
                                </xsl:if>
                                <xsl:value-of select="$address/n1:country" />
                            </xsl:if>
                        </p>
                    </div>

                </xsl:when>
                <xsl:otherwise>
                    <div class="address-group-content">
                        <span class="generated-text">
                            <xsl:text>&lt;&gt;</xsl:text>
                        </span>
                    </div>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>
    <!-- show-telecom -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-telecom">
        <xsl:param name="telecom" />
        <div class="address-group">
            <xsl:choose>
                <xsl:when test="$telecom">
                    <xsl:variable name="type" select="substring-before($telecom/@value, ':')" />
                    <xsl:variable name="value" select="substring-after($telecom/@value, ':')" />
                    <xsl:if test="$type">
                        <div class="address-group-header">
                            <xsl:call-template name="translateTelecomCode">
                                <xsl:with-param name="code" select="$type" />
                            </xsl:call-template>
                            <xsl:text>: </xsl:text>
                            <xsl:if test="@use">
                                <xsl:text> (</xsl:text>
                                <xsl:call-template name="translateTelecomCode">
                                    <xsl:with-param name="code" select="@use" />
                                </xsl:call-template>
                                <xsl:text>) </xsl:text>
                            </xsl:if>
                            <xsl:value-of select="$value" />
                        </div>
                    </xsl:if>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>&lt;&gt;</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </xsl:template>
    <!-- show-recipientType -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-recipientType">
        <xsl:param name="typeCode" />
        <xsl:choose>
            <xsl:when test="$typeCode = 'PRCP'">Primary Recipient:</xsl:when>
            <xsl:when test="$typeCode = 'TRC'">Secondary Recipient:</xsl:when>
            <xsl:otherwise>Recipient:</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- Convert Telecom URL to display text -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="translateTelecomCode">
        <xsl:param name="code" />
        <!--xsl:value-of select="document('voc.xml')/systems/system[@root=$code/@codeSystem]/code[@value=$code/@code]/@displayName"/-->
        <!--xsl:value-of select="document('codes.xml')/*/code[@code=$code]/@display"/-->
        <xsl:choose>
            <!-- lookup table Telecom URI -->
            <xsl:when test="$code = 'tel'">
                <xsl:text>tel</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'fax'">
                <xsl:text>fax</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'http'">
                <xsl:text>web</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'mailto'">
                <xsl:text>email</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'H'">
                <xsl:text>Home</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'url'">
                <xsl:text>URL</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'HV'">
                <xsl:text>Vacation Home</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'HP'">
                <xsl:text>Primary Home</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'WP'">
                <xsl:text>Work Place</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'MC'">
                <xsl:text>Mobile Contact</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'DIR'">
                <xsl:text>Direct</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'PUB'">
                <xsl:text>Public</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'AS'">
                <xsl:text>Answering Service</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'PG'">
                <xsl:text>Pager</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'TMP'">
                <xsl:text>Temporary</xsl:text>
            </xsl:when>
            <xsl:when test="$code = 'BAD'">
                <xsl:text>Bad or Old</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>{$code='</xsl:text>
                <xsl:value-of select="$code" />
                <xsl:text>'?}</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- convert RoleClassAssociative code to display text -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="translateRoleAssoCode">
        <xsl:param name="classCode" />
        <xsl:param name="code" />
        <xsl:choose>
            <xsl:when test="$classCode = 'AFFL'">
                <xsl:text>affiliate</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'AGNT'">
                <xsl:text>agent</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'ASSIGNED'">
                <xsl:text>assigned entity</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'COMPAR'">
                <xsl:text>commissioning party</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'CON'">
                <xsl:text>contact</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'ECON'">
                <xsl:text>emergency contact</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'NOK'">
                <xsl:text>next of kin</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'SGNOFF'">
                <xsl:text>signing authority</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'GUARD'">
                <xsl:text>guardian</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'GUAR'">
                <xsl:text>guardian</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'CIT'">
                <xsl:text>citizen</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'COVPTY'">
                <xsl:text>covered party</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'PRS'">
                <xsl:text>personal relationship</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'CAREGIVER'">
                <xsl:text>care giver</xsl:text>
            </xsl:when>
            <xsl:when test="$classCode = 'PROV'">
                <xsl:text>healthcare provider</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>{$classCode='</xsl:text>
                <xsl:value-of select="$classCode" />
                <xsl:text>'?}</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="($code/@code) and ($code/@codeSystem = '2.16.840.1.113883.5.111')">
            <xsl:text> </xsl:text>
            <xsl:choose>
                <xsl:when test="$code/@code = 'FTH'">
                    <xsl:text>(Father)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'MTH'">
                    <xsl:text>(Mother)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'NPRN'">
                    <xsl:text>(Natural parent)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'STPPRN'">
                    <xsl:text>(Step parent)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'SONC'">
                    <xsl:text>(Son)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'DAUC'">
                    <xsl:text>(Daughter)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'CHILD'">
                    <xsl:text>(Child)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'EXT'">
                    <xsl:text>(Extended family member)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'NBOR'">
                    <xsl:text>(Neighbor)</xsl:text>
                </xsl:when>
                <xsl:when test="$code/@code = 'SIGOTHR'">
                    <xsl:text>(Significant other)</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:text>{$code/@code='</xsl:text>
                    <xsl:value-of select="$code/@code" />
                    <xsl:text>'?}</xsl:text>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:if>
    </xsl:template>
    <!-- show time -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-time">
        <xsl:param name="datetime" />
        <xsl:choose>
            <xsl:when test="not($datetime)">
                <xsl:call-template name="formatDateTime">
                    <xsl:with-param name="date" select="@value" />
                </xsl:call-template>
                <xsl:text> </xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="formatDateTime">
                    <xsl:with-param name="date" select="$datetime/@value" />
                </xsl:call-template>
                <xsl:text> </xsl:text>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- paticipant facility and date -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="facilityAndDates">
        <table class="header_table">
            <tbody>
                <!-- facility id -->
                <tr>
                    <td class="td_header_role_name">
                        <span class="td_label">
                            <xsl:text>Facility ID</xsl:text>
                        </span>
                    </td>
                    <td class="td_header_role_value">
                        <xsl:choose>
                            <xsl:when test="count(/n1:ClinicalDocument/n1:participant[@typeCode = 'LOC'][@contextControlCode = 'OP']/n1:associatedEntity[@classCode = 'SDLOC']/n1:id) &gt; 0">
                                <!-- change context node -->
                                <xsl:for-each select="/n1:ClinicalDocument/n1:participant[@typeCode = 'LOC'][@contextControlCode = 'OP']/n1:associatedEntity[@classCode = 'SDLOC']/n1:id">
                                    <xsl:call-template name="show-id" />
                                    <!-- change context node again, for the code -->
                                    <xsl:for-each select="../n1:code">
                                        <xsl:text> (</xsl:text>
                                        <xsl:call-template name="show-code">
                                            <xsl:with-param name="code" select="." />
                                        </xsl:call-template>
                                        <xsl:text>)</xsl:text>
                                    </xsl:for-each>
                                </xsl:for-each>
                            </xsl:when>
                            <xsl:otherwise> Not available </xsl:otherwise>
                        </xsl:choose>
                    </td>
                </tr>
                <!-- Period reported -->
                <tr>
                    <td class="td_header_role_name">
                        <span class="td_label">
                            <xsl:text>First day of period reported</xsl:text>
                        </span>
                    </td>
                    <td class="td_header_role_value">
                        <xsl:call-template name="show-time">
                            <xsl:with-param name="datetime" select="/n1:ClinicalDocument/n1:documentationOf/n1:serviceEvent/n1:effectiveTime/n1:low" />
                        </xsl:call-template>
                    </td>
                </tr>
                <tr>
                    <td class="td_header_role_name">
                        <span class="td_label">
                            <xsl:text>Last day of period reported</xsl:text>
                        </span>
                    </td>
                    <td class="td_header_role_value">
                        <xsl:call-template name="show-time">
                            <xsl:with-param name="datetime" select="/n1:ClinicalDocument/n1:documentationOf/n1:serviceEvent/n1:effectiveTime/n1:high" />
                        </xsl:call-template>
                    </td>
                </tr>
            </tbody>
        </table>
    </xsl:template>
    <!-- SG: Add for parent/guardian -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-guardian">
        <xsl:param name="guard" />
        <xsl:choose>
            <xsl:when test="$guard/n1:guardianPerson/n1:name">
                <xsl:call-template name="show-name">
                    <xsl:with-param name="name" select="$guard/n1:guardianPerson/n1:name" />
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- show assignedEntity -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-assignedEntity">
        <xsl:param name="asgnEntity" />
        <xsl:choose>
            <xsl:when test="$asgnEntity/n1:assignedPerson/n1:name">
                <xsl:call-template name="show-name">
                    <xsl:with-param name="name" select="$asgnEntity/n1:assignedPerson/n1:name" />
                </xsl:call-template>
                <xsl:if test="$asgnEntity/n1:representedOrganization/n1:name">
                    <xsl:text> of </xsl:text>
                    <xsl:value-of select="$asgnEntity/n1:representedOrganization/n1:name" />
                </xsl:if>
            </xsl:when>
            <xsl:when test="$asgnEntity/n1:representedOrganization">
                <xsl:value-of select="$asgnEntity/n1:representedOrganization/n1:name" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:for-each select="$asgnEntity/n1:id">
                    <xsl:call-template name="show-id" />
                    <xsl:choose>
                        <xsl:when test="position() != last()">
                            <xsl:text>, </xsl:text>
                        </xsl:when>
                        <xsl:otherwise>
                            <br />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- show relatedEntity -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-relatedEntity">
        <xsl:param name="relatedEntity" />
        <xsl:choose>
            <xsl:when test="$relatedEntity/n1:relatedPerson/n1:name">
                <xsl:call-template name="show-name">
                    <xsl:with-param name="name" select="$relatedEntity/n1:relatedPerson/n1:name" />
                </xsl:call-template>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- show associatedEntity -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-associatedEntity">
        <xsl:param name="assoEntity" />
        <!-- SG: This shouldn't be a choice, can be a combination of these things -->
        <!--<xsl:choose>-->
        <!--      <xsl:when test="$assoEntity/n1:associatedPerson">-->
        <xsl:for-each select="$assoEntity/n1:associatedPerson/n1:name">
            <xsl:call-template name="show-name">
                <xsl:with-param name="name" select="." />
            </xsl:call-template><br />
        </xsl:for-each>
        <!--</xsl:when>-->
        <!--      <xsl:when test="$assoEntity/n1:scopingOrganization">-->
        <xsl:for-each select="$assoEntity/n1:scopingOrganization">
            <xsl:if test="n1:name">
                <xsl:call-template name="show-name">
                    <xsl:with-param name="name" select="n1:name" />
                </xsl:call-template>
                <br />
            </xsl:if>
            <xsl:if test="n1:standardIndustryClassCode">
                <xsl:value-of select="n1:standardIndustryClassCode/@displayName" />
                <xsl:text> code:</xsl:text>
                <xsl:value-of select="n1:standardIndustryClassCode/@code" />
            </xsl:if>
            <br />
        </xsl:for-each>
        <!--</xsl:when>-->
        <!--      <xsl:when test="$assoEntity/n1:code">--> (<xsl:call-template name="show-code">
            <xsl:with-param name="code" select="$assoEntity/n1:code" />
        </xsl:call-template>) <!--</xsl:when>-->
        <!--      <xsl:when test="$assoEntity/n1:id">-->
        <xsl:value-of select="$assoEntity/n1:id/@extension" />
        <xsl:text> </xsl:text>
        <xsl:value-of select="$assoEntity/n1:id/@root" />
        <!--</xsl:when>-->
        <!--</xsl:choose>-->
    </xsl:template>
    <!-- show code
     if originalText present, return it, otherwise, check and return attribute: display name
     -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-code">
        <xsl:param name="code" />
        <xsl:variable name="this-codeSystem">
            <xsl:value-of select="$code/@codeSystem" />
        </xsl:variable>
        <xsl:variable name="this-code">
            <xsl:value-of select="$code/@code" />
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$code/n1:originalText">
                <xsl:value-of select="$code/n1:originalText" />
            </xsl:when>
            <xsl:when test="$code/@displayName">
                <xsl:value-of select="$code/@displayName" />
            </xsl:when>

            <xsl:otherwise>
                <xsl:value-of select="$this-code" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- show classCode -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-actClassCode">
        <xsl:param name="clsCode" />
        <xsl:choose>
            <xsl:when test="$clsCode = 'ACT'">
                <xsl:text>healthcare service</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'ACCM'">
                <xsl:text>accommodation</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'ACCT'">
                <xsl:text>account</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'ACSN'">
                <xsl:text>accession</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'ADJUD'">
                <xsl:text>financial adjudication</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'CONS'">
                <xsl:text>consent</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'CONTREG'">
                <xsl:text>container registration</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'CTTEVENT'">
                <xsl:text>clinical trial timepoint event</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'DISPACT'">
                <xsl:text>disciplinary action</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'ENC'">
                <xsl:text>encounter</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'INC'">
                <xsl:text>incident</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'INFRM'">
                <xsl:text>inform</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'INVE'">
                <xsl:text>invoice element</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'LIST'">
                <xsl:text>working list</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'MPROT'">
                <xsl:text>monitoring program</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'PCPR'">
                <xsl:text>care provision</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'PROC'">
                <xsl:text>procedure</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'REG'">
                <xsl:text>registration</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'REV'">
                <xsl:text>review</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'SBADM'">
                <xsl:text>substance administration</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'SPCTRT'">
                <xsl:text>specimen treatment</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'SUBST'">
                <xsl:text>substitution</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'TRNS'">
                <xsl:text>transportation</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'VERIF'">
                <xsl:text>verification</xsl:text>
            </xsl:when>
            <xsl:when test="$clsCode = 'XACT'">
                <xsl:text>financial transaction</xsl:text>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- show participationType -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-participationType">
        <xsl:param name="ptype" />
        <xsl:choose>
            <xsl:when test="$ptype = 'PPRF'">
                <xsl:text>primary performer</xsl:text>
            </xsl:when>
            <xsl:when test="$ptype = 'PRF'">
                <xsl:text>performer</xsl:text>
            </xsl:when>
            <xsl:when test="$ptype = 'VRF'">
                <xsl:text>verifier</xsl:text>
            </xsl:when>
            <xsl:when test="$ptype = 'SPRF'">
                <xsl:text>secondary performer</xsl:text>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <!-- show participationFunction -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-participationFunction">
        <xsl:param name="pFunction" />
        <xsl:choose>
            <!-- From the HL7 v3 ParticipationFunction code system -->
            <xsl:when test="$pFunction = 'ADMPHYS'">
                <xsl:text>(admitting physician)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'ANEST'">
                <xsl:text>(anesthesist)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'ANRS'">
                <xsl:text>(anesthesia nurse)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'ATTPHYS'">
                <xsl:text>(attending physician)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'DISPHYS'">
                <xsl:text>(discharging physician)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'FASST'">
                <xsl:text>(first assistant surgeon)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'MDWF'">
                <xsl:text>(midwife)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'NASST'">
                <xsl:text>(nurse assistant)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'PCP'">
                <xsl:text>(primary care physician)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'PRISURG'">
                <xsl:text>(primary surgeon)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'RNDPHYS'">
                <xsl:text>(rounding physician)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'SASST'">
                <xsl:text>(second assistant surgeon)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'SNRS'">
                <xsl:text>(scrub nurse)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'TASST'">
                <xsl:text>(third assistant)</xsl:text>
            </xsl:when>
            <!-- From the HL7 v2 Provider Role code system (2.16.840.1.113883.12.443) which is used by HITSP -->
            <xsl:when test="$pFunction = 'CP'">
                <xsl:text>(consulting provider)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'PP'">
                <xsl:text>(primary care provider)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'RP'">
                <xsl:text>(referring provider)</xsl:text>
            </xsl:when>
            <xsl:when test="$pFunction = 'MP'">
                <xsl:text>(medical home provider)</xsl:text>
            </xsl:when>
        </xsl:choose>
    </xsl:template>
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="formatDateTime">
        <xsl:param name="date" />
        <!-- month -->
        <xsl:variable name="month" select="substring($date, 5, 2)" />
        <!-- day -->
        <xsl:value-of select="$month" />
        <xsl:text>/</xsl:text>
        <xsl:choose>
            <xsl:when test="substring($date, 7, 1) = &quot;0&quot;">
                <xsl:value-of select="substring($date, 8, 1)" />
                <xsl:text>/</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="substring($date, 7, 2)" />
                <xsl:text>/</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <!-- year -->
        <xsl:value-of select="substring($date, 1, 4)" />
        <!-- time and US timezone -->
        <xsl:if test="string-length($date) &gt; 8">
            <!-- time -->
            <xsl:variable name="time">
                <xsl:value-of select="substring($date, 9, 6)" />
            </xsl:variable>
            <xsl:variable name="hh">
                <xsl:value-of select="substring($time, 1, 2)" />
            </xsl:variable>
            <xsl:variable name="mm">
                <xsl:value-of select="substring($time, 3, 2)" />
            </xsl:variable>
            <xsl:variable name="ss">
                <xsl:value-of select="substring($time, 5, 2)" />
            </xsl:variable>
            <xsl:if test="(string-length($hh) &gt; 1 and not($hh = '00')) or (string-length($mm) &gt; 1 and not($mm = '00'))">
                <xsl:text>, </xsl:text>
                <xsl:value-of select="$hh" />
                <xsl:if test="string-length($mm) &gt; 1 and not(contains($mm, '-')) and not(contains($mm, '+'))">
                    <xsl:text>:</xsl:text>
                    <xsl:value-of select="$mm" />
                </xsl:if>
            </xsl:if>
        </xsl:if>
    </xsl:template>
    <!-- convert to lower case -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="caseDown">
        <xsl:param name="data" />
        <xsl:if test="$data">
            <xsl:value-of select="translate($data, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')" />
        </xsl:if>
    </xsl:template>
    <!-- convert to upper case -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="caseUp">
        <xsl:param name="data" />
        <xsl:if test="$data">
            <xsl:value-of select="translate($data, 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')" />
        </xsl:if>
    </xsl:template>
    <!-- convert first character to upper case -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="firstCharCaseUp">
        <xsl:param name="data" />
        <xsl:if test="$data">
            <xsl:call-template name="caseUp">
                <xsl:with-param name="data" select="substring($data, 1, 1)" />
            </xsl:call-template>
            <xsl:value-of select="substring($data, 2)" />
        </xsl:if>
    </xsl:template>
    <!-- show-noneFlavor -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="show-noneFlavor">
        <xsl:param name="nf" />
        <xsl:choose>
            <xsl:when test="$nf = 'NI'">
                <xsl:text>no information</xsl:text>
            </xsl:when>
            <xsl:when test="$nf = 'INV'">
                <xsl:text>invalid</xsl:text>
            </xsl:when>
            <xsl:when test="$nf = 'MSK'">
                <xsl:text>masked</xsl:text>
            </xsl:when>
            <xsl:when test="$nf = 'NA'">
                <xsl:text>not applicable</xsl:text>
            </xsl:when>
            <xsl:when test="$nf = 'UNK'">
                <xsl:text>unknown</xsl:text>
            </xsl:when>
            <xsl:when test="$nf = 'OTH'">
                <xsl:text>other</xsl:text>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- convert common OIDs for Identifiers -->
    <xsl:template xmlns:n1="urn:hl7-org:v3" xmlns:in="urn:lantana-com:inline-variable-data" name="translate-id-type">
        <xsl:param name="id-oid" />
        <xsl:choose>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.1'">
                <xsl:text>United States Social Security Number</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.6'">
                <xsl:text>NPI (US)</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.2'">
                <xsl:text>Alaska Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.1'">
                <xsl:text>Alabama Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.5'">
                <xsl:text>Arkansas Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.4'">
                <xsl:text>Arizona Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.6'">
                <xsl:text>California Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.8'">
                <xsl:text>Colorado Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.9'">
                <xsl:text>Connecticut Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.11'">
                <xsl:text>DC Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.10'">
                <xsl:text>Delaware Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.12'">
                <xsl:text>Florida Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.13'">
                <xsl:text>Georgia Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.15'">
                <xsl:text>Hawaii Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.18'">
                <xsl:text>Indiana Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.19'">
                <xsl:text>Iowa Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.16'">
                <xsl:text>Idaho Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.17'">
                <xsl:text>Illinois Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.20'">
                <xsl:text>Kansas Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.21'">
                <xsl:text>Kentucky Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.22'">
                <xsl:text>Louisiana Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.25'">
                <xsl:text>Massachusetts Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.24'">
                <xsl:text>Maryland Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.23'">
                <xsl:text>Maine Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.26'">
                <xsl:text>Michigan Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.27'">
                <xsl:text>Minnesota Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.29'">
                <xsl:text>Missouri Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.28'">
                <xsl:text>Mississippi Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.30'">
                <xsl:text>Montana Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.36'">
                <xsl:text>New York Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.37'">
                <xsl:text>North Carolina Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.38'">
                <xsl:text>North Dakota Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.31'">
                <xsl:text>Nebraska Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.33'">
                <xsl:text>New Hampshire Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.34'">
                <xsl:text>New Jersey Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.35'">
                <xsl:text>New Mexico Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.32'">
                <xsl:text>Nevada Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.39'">
                <xsl:text>Ohio Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.40'">
                <xsl:text>Oklahoma Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.41'">
                <xsl:text>Oregon Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.42'">
                <xsl:text>Pennsylvania Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.44'">
                <xsl:text>Rhode Island Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.45'">
                <xsl:text>South Carolina Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.46'">
                <xsl:text>South Dakota Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.47'">
                <xsl:text>Tennessee Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.48'">
                <xsl:text>Texas Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.49'">
                <xsl:text>Utah Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.51'">
                <xsl:text>Virginia Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.50'">
                <xsl:text>Vermont Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.53'">
                <xsl:text>Washington Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.55'">
                <xsl:text>Wisconsin Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.54'">
                <xsl:text>West Virginia Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.4.3.56'">
                <xsl:text>Wyoming Driver's License</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.12.203'">
                <xsl:text>Identifier Type (HL7)</xsl:text>
            </xsl:when>

            <!-- Axesson-specific OIDs -->
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.1'">
                <xsl:text>Associated Pathology Medical Group</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.2'">
                <xsl:text>ATMS</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.3'">
                <xsl:text>AXESSON TRANSCRIPTION</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.4'">
                <xsl:text>Axesson Word Doc Transcriptions</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.5'">
                <xsl:text>CrossTx</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.9'">
                <xsl:text>Dignity Health Medical Group</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.9.4.1'">
                <xsl:text>Dignity Boulder Creek</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.10'">
                <xsl:text>Dominican Santa Cruz Hospital</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.10.4.1'">
                <xsl:text>Dignity Internal Medicine</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.10.4.2'">
                <xsl:text>Dignity Pediatrics</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50023'">
                <xsl:text>Joydip Bhattacharya</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50003'">
                <xsl:text>Balance Health of Ben Lomond</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50040'">
                <xsl:text>Edward T Bradbury MD A Prof. Corp</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50014'">
                <xsl:text>Bayview Gastroenterology</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50037'">
                <xsl:text>Peggy Chen, M.D.</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50004'">
                <xsl:text>Central Coast Sleep Disorders Center</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50024'">
                <xsl:text>Central Coast Oncology and Hematology</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50002'">
                <xsl:text>Albert Crevello, MD</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50021'">
                <xsl:text>Diabetes Health Center</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50005'">
                <xsl:text>Foot Doctors of Santa Cruz</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50032'">
                <xsl:text>Maria Granthom, M.D.</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50006'">
                <xsl:text>Gastroenterology</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50030'">
                <xsl:text>Harbor Medical Group</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50033'">
                <xsl:text>Monterey Bay Gastroenterology</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50034'">
                <xsl:text>Monterey Bay Urology</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '1.2.840.114398.1.35.1'">
                <xsl:text>No More Clipboard</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50010'">
                <xsl:text>Plazita Medical Clinic</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50009'">
                <xsl:text>Pajaro Valley Neurolgy Medical Associates</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50007'">
                <xsl:text>Milan Patel, MD</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50039'">
                <xsl:text>Santa Cruz Pulmonary Medical Group</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50038'">
                <xsl:text>Rio Del Mar Medical Clinic</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50011'">
                <xsl:text>Romo, Mary-Lou</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50027'">
                <xsl:text>Santa Cruz Office Santa Cruz Ear Nose and Throat Medical Group</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50012'">
                <xsl:text>Scotts Valley Medical Clinic</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50041'">
                <xsl:text>Simkin, Josefa MD</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.3.1.50013'">
                <xsl:text>Vu, Thanh</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.6'">
                <xsl:text>Bioreference Labs</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.7'">
                <xsl:text>BSCA Claims Data</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.8'">
                <xsl:text>CCSDC</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.11'">
                <xsl:text>Cedar Medical Clinic</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.12'">
                <xsl:text>Cedar Medical Clinic</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.13'">
                <xsl:text>DIANON</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.14'">
                <xsl:text>ANDREA EDWARDS MD</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.15'">
                <xsl:text>Elysium</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.16'">
                <xsl:text>Family Doctors of Santa Cruz</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.17'">
                <xsl:text>Hurray, Alvie</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.18'">
                <xsl:text>Hunter</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.19'">
                <xsl:text>LABCORP</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.20'">
                <xsl:text>LABCORP UNKNOWN</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.21'">
                <xsl:text>Melissa Lopez-Bermejo, MD</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.22'">
                <xsl:text>Monterey Bay Family Physicians</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.23'">
                <xsl:text>Medtek</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.24'">
                <xsl:text>Mirth Support Testing Facility</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.25'">
                <xsl:text>NSIGHT</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.26'">
                <xsl:text>NwHIN</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.27'">
                <xsl:text>OrthoNorCal</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.28'">
                <xsl:text>Pajaro Health Center</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.29'">
                <xsl:text>Pajaro Valley Medical Clinic</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.30'">
                <xsl:text>Pajaro Valley Personal Health</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.31'">
                <xsl:text>PMG</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.32'">
                <xsl:text>QUEST</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.33'">
                <xsl:text>Radiology Medical Group</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.34'">
                <xsl:text>Resneck-Sannes, L. David MD</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.35'">
                <xsl:text>Salud Para La Gente</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.36'">
                <xsl:text>SBWTest</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.37'">
                <xsl:text>Quest Diagnostics SC</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.38'">
                <xsl:text>Santa Cruz County Health Services Agency</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.39'">
                <xsl:text>Santa Cruz County Mental Health</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.40'">
                <xsl:text>SCHIEAUTH</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.41'">
                <xsl:text>Santa Cruz HIE</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.42'">
                <xsl:text>Santa Cruz Nephrology Medical Group, Inc</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.43'">
                <xsl:text>Santa Cruz Surgery Center</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.44'">
                <xsl:text>Quest Diagnostics SJ</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.45'">
                <xsl:text>Stanford Lab</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.46'">
                <xsl:text>Unknown</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.47'">
                <xsl:text>Watsonville Community Hospital</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.3.290.2.1.48'">
                <xsl:text>zzBAD_REFERENCE_FACILITY</xsl:text>
            </xsl:when>



            <!-- Example OIDS -->
            <xsl:when test="$id-oid = '2.16.840.1.113883.19.5'">
                <xsl:text>Meaningless identifier, not to be used for any actual entities. Examples only.</xsl:text>
            </xsl:when>
            <xsl:when test="$id-oid = '2.16.840.1.113883.19.5.99999.2'">
                <xsl:text>Meaningless identifier, not to be used for any actual entities. Examples only.</xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text>OID: </xsl:text>
                <xsl:value-of select="$id-oid" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template xmlns:xs="http://www.w3.org/2001/XMLSchema" name="lantana-css">
        <style>
            /* Catch all for the document */
            .cda-render {
                font-family: CenturyGothic, sans-serif;
                /*font-size:1.25em;*/
            }

            /* One-off - CDA Document Title */
            .cda-render h1.cda-title {
                color: #b3623d;
                font-size: 1.5em;
                font-weight: bold;
                text-align: center;
                text-transform: uppercase;
            }


            /* One-off - Table of contents formatting */
            .cda-render .toc-header-container {
                padding-top: 0.5em;
                border-bottom-width: 0.1em;
                border-bottom-style: solid;
                border-bottom-color: #b3623d;
                padding-bottom: 0.5em;
            }

            .cda-render .toc-header {
                text-transform: uppercase;
                color: #b3623d;
                font-weight: bold;
            }

            .cda-render .toc {
                margin-top: 3em;
                padding: 0px 15px;
            }

            .cda-render .toc-box {

            }


            /* One-off - Patient Name Formatting */
            .cda-render .patient-name {
                color: #336b7a;
                font-size: 1.25em;
                font-weight: bold;
            }

            /* Patient ID Formatting */
            .patient-id {
                border-left-width: 0.15em;
                border-left-style: solid;
                border-left-color: #478B95;
            }
            /* Re-usable - Section-Title */
            .cda-render .section-title {
                color: #336b7a;
                font-size: 1.09em;
                font-weight: bold;
                text-transform: uppercase;
            }

            /* Re-usable - Attribute title */
            .cda-render .attribute-title {
                color: #000000;
                font-weight: bold;
                font-size: 1.04em;
            }


            /***** Header Grouping */
            .cda-render .header {
                border-bottom-width: 0.1em;
                border-bottom-style: solid;
                border-bottom-color: #1B6373;
                padding-bottom: 0.5em;
            }

            .cda-render .header-group-content {
                margin-left: 1em;
                padding-left: 0.5em;
                border-left-width: 0.15em;
                border-left-style: solid;
                border-left-color: #478B95;
            }

            .cda-render .tight {
                margin: 0;
            }
            .cda-render .generated-text {
                white-space: no-wrap;
                margin: 0em;
                color: #B0592C;
                font-style: italic;
            }
            .cda-render .bottom {
                border-top-width: 0.2em;
                border-top-color: #B0592C;
                border-top-style: solid;
            }

            /***** Table of Contents Attributes */
            /* Table of contents entry */
            .cda-render .lantana-toc {
                text-transform: uppercase;
            }

            .cda-render .bold {
                font-weight: bold;
            }

            .cda-render .active {
                border-right-color: #336b7a;
                border-right-style: solid;
                border-left-color: #336b7a;
                border-left-style: solid;
                background-color: #eee;
            }

            #navbar-list-cda {
                overflow: auto;
            }</style>
    </xsl:template>
    <xsl:template xmlns:xs="http://www.w3.org/2001/XMLSchema" name="lantana-js">
        <script type="text/javascript">
        alert("Loading Lantana JS");
        $(document).ready(function () {
            $('#navbar-list-cda').height($(window).height() -100);
        });
        $(window).resize(function () {
            $('#navbar-list-cda').height($(window).height() -100);
        });

        $(document).ready(function () {
            $('#navbar-list-cda').height($(window).height() -100);
        });

        $(window).resize(function () {
            $('#navbar-list-cda').height($(window).height() -100);
        });

        $(document).ready(function () {
            $('.cda-render a[href*="#"]:not([href="#"])').bind('click.smoothscroll', function (e) {
                e.preventDefault();

                var target = this.hash,
                $target = $(target);

                $('html, body').stop().animate({
                    'scrollTop': $target.offset().top
                },
                1000, 'swing', function () {
                    window.location.hash = target;

                    // lets add a div in the background
                    $('&amp;lt;div /&amp;gt;').css({
                        'background': '#336b7a'
                    }).prependTo($target).fadeIn('fast', function () {
                        $(this).fadeOut('fast', function () {
                            $(this).remove();
                        });
                    });
                });
            });
        });

        $(function () {
            $("#navbar-list-cda-sortable").sortable();
            $("#navbar-list-cda-sortable").disableSelection();
        });

        $(function () {
            var $nav = $('#navbar-list-cda-sortable');
            var $content = $('#doc-clinical-info');
            var $originalContent = $content.clone();
            $nav.sortable({
                update: function (e) {
                    $content.empty();
                    $nav.find('a').each(function () {
                        $content.append($originalContent.clone().find($(this).attr('href')).parent ());
                    });

                    $('[data-spy="scroll"]').each(function () {
                        var $spy = $(this).scrollspy('refresh')
                    })
                }
            });
        });</script>
    </xsl:template>
    <xsl:template name="jquery">
      <script type="text/javascript" src="https://code.jquery.com/jquery-1.12.1.min.js"></script>
    </xsl:template>
    <xsl:template name="jquery-ui">
      <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.12.0/jquery-ui.min.js"></script>
    </xsl:template>
    <xsl:template name="bootstrap-css">
      <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" />
    </xsl:template>
    <xsl:template name="bootstrap-javascript">
      <script type="text/javascript" src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js"></script>
    </xsl:template>
</xsl:stylesheet>
