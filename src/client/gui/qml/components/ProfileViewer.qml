import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#f0f0f0"
    
    signal backClicked()
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 15

        // Заголовок
        Text {
            text: "Просмотр профилей"
            font.pixelSize: 18
            font.bold: true
            Layout.alignment: Qt.AlignHCenter
            Layout.bottomMargin: 10
        }

        // Инструкция
        Text {
            text: "Список доступных профилей и их комментарии"
            font.pixelSize: 14
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Layout.bottomMargin: 5
        }

        // Список профилей
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: profileList
                anchors.fill: parent
                model: profileManager.profilesList
                spacing: 8

                delegate: Item {
                    width: parent.width
                    height: 60
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 5
                        spacing: 2
                        
                        Text {
                            text: modelData
                            font.pixelSize: 16
                            font.bold: true
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                        
                        Text {
                            text: "Комментарий: " + (profileManager.getProfileComment(modelData) || "Отсутствует")
                            font.pixelSize: 14
                            color: "#666666"
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            wrapMode: Text.WordWrap
                        }
                    }
                    
                    // Разделительная линия
                    Rectangle {
                        width: parent.width
                        height: 1
                        color: "#e0e0e0"
                        anchors.bottom: parent.bottom
                    }
                }
            }
        }

        // Кнопка "Назад"
        Button {
            text: "Назад"
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            flat: true
            background: Rectangle {
                color: parent.hovered ? "#e0e0e0" : "#ffffff"
                border.color: "#d0d0d0"
                radius: 2
            }
            onClicked: root.backClicked()
        }
    }
} 