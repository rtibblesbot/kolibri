package org.learningequality.Kolibri.discovery;

import java.util.Collections;
import java.util.List;
import java.util.Map;

final class MdnsMessage {

  static final int TYPE_A = 1;
  static final int TYPE_PTR = 12;
  static final int TYPE_TXT = 16;
  static final int TYPE_SRV = 33;

  static final class Question {
    private final String name;
    private final int type;

    Question(String name, int type) {
      this.name = name;
      this.type = type;
    }

    String getName() {
      return name;
    }

    int getType() {
      return type;
    }
  }

  static final class Record {
    private final String name;
    private final int type;
    private final String target;
    private final int port;
    private final String address;
    private final Map<String, String> txt;

    private Record(
        String name, int type, String target, int port, String address, Map<String, String> txt) {
      this.name = name;
      this.type = type;
      this.target = target;
      this.port = port;
      this.address = address;
      this.txt = txt;
    }

    String getName() {
      return name;
    }

    int getType() {
      return type;
    }

    /** The PTR or SRV target name; null for other types. */
    String getTarget() {
      return target;
    }

    /** The SRV port; 0 for other types. */
    int getPort() {
      return port;
    }

    /** The A record's dotted IPv4 address; null for other types. */
    String getAddress() {
      return address;
    }

    /** The TXT entries; empty for other types. */
    Map<String, String> getTxt() {
      return txt;
    }
  }

  private final boolean response;
  private final List<Question> questions;
  private final List<Record> records;

  private MdnsMessage(boolean response, List<Question> questions, List<Record> records) {
    this.response = response;
    this.questions = questions;
    this.records = records;
  }

  static byte[] query(String name, int... types) {
    return new byte[0];
  }

  /**
   * @throws IllegalArgumentException when the bytes are not a well-formed DNS message
   */
  static MdnsMessage parse(byte[] data, int length) {
    return new MdnsMessage(false, Collections.emptyList(), Collections.emptyList());
  }

  boolean isResponse() {
    return response;
  }

  List<Question> getQuestions() {
    return questions;
  }

  /** Answer, authority and additional records, in packet order. */
  List<Record> getRecords() {
    return records;
  }
}
